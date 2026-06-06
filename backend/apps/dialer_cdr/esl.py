"""
FreeSWITCH ESL (Event Socket Library) integration.

Uses a minimal *synchronous* inbound-socket client built on stdlib sockets.
We intentionally do NOT use greenswitch here: greenswitch is gevent-based and
hangs ("This operation would block forever") when called from contexts that
don't drive a gevent loop — i.e. Celery workers and Daphne's thread executors,
which is exactly where this code runs. A plain blocking socket is correct for
request/response commands (originate, uuid_*, sofia_contact, etc.).
"""
from __future__ import annotations
import logging
import socket
import threading
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class ESLResponse:
    """Parsed ESL reply. `headers` is the header dict, `data` is the body text."""
    __slots__ = ('headers', 'data')

    def __init__(self, headers: dict, data: str = ''):
        self.headers = headers
        self.data = data


class ESLClient:
    """
    Minimal synchronous inbound ESL client.

    Only the request/response subset is implemented (no async event
    subscription), which is all the dialer needs. Thread-safe via a lock so
    Daphne thread-executor calls and the Celery worker can share one instance.
    """

    def __init__(self, host: str, port: int, password: str, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._fp = None
        self._lock = threading.Lock()
        self.connected = False

    # ── connection ──────────────────────────────────────────────
    def connect(self):
        self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self._sock.settimeout(self.timeout)
        self._fp = self._sock.makefile('rb')

        # FreeSWITCH greets with "Content-Type: auth/request"
        self._read_event()
        # Authenticate
        self._send_raw(f'auth {self.password}')
        reply = self._read_event()
        if '+OK' not in reply.headers.get('Reply-Text', ''):
            self.close()
            raise ConnectionError(f"ESL auth rejected: {reply.headers.get('Reply-Text')}")
        self.connected = True

    def close(self):
        self.connected = False
        try:
            if self._fp:
                self._fp.close()
        except Exception:
            pass
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        self._fp = None
        self._sock = None

    # ── low-level IO ────────────────────────────────────────────
    def _send_raw(self, command: str):
        # ESL commands are terminated by a double newline
        self._sock.sendall((command.rstrip('\n') + '\n\n').encode('utf-8'))

    def _read_event(self) -> ESLResponse:
        headers = {}
        while True:
            line = self._fp.readline()
            if not line:
                raise ConnectionError('ESL connection closed by peer')
            line = line.decode('utf-8', 'replace').rstrip('\r\n')
            if line == '':
                break  # end of headers
            if ':' in line:
                key, val = line.split(':', 1)
                headers[key.strip()] = val.strip()

        data = ''
        content_length = headers.get('Content-Length')
        if content_length:
            n = int(content_length)
            body = self._fp.read(n)
            data = (body or b'').decode('utf-8', 'replace')

        # bgapi success returns "+OK Job-UUID: <uuid>" in Reply-Text
        reply_text = headers.get('Reply-Text', '')
        if 'Job-UUID:' in reply_text:
            headers['Job-UUID'] = reply_text.split('Job-UUID:', 1)[1].strip()

        return ESLResponse(headers, data)

    # ── public API ──────────────────────────────────────────────
    def send(self, command: str) -> ESLResponse:
        """Send a command and return the reply. Reconnects once if the socket died."""
        with self._lock:
            for attempt in (1, 2):
                try:
                    if not self.connected:
                        self.connect()
                    self._send_raw(command)
                    return self._read_event()
                except (OSError, ConnectionError) as exc:
                    logger.warning(f"ESL send failed (attempt {attempt}): {exc}")
                    self.close()
                    if attempt == 2:
                        raise
            raise ConnectionError('ESL send failed')


# Connection pool - one client per FS node
_connections: dict[str, ESLClient] = {}


def get_esl_connection(node: str = 'fs1') -> Optional[ESLClient]:
    """
    Get or create a synchronous ESL client for the given FreeSWITCH node.
    Cached and reused; reconnects automatically when stale.
    """
    existing = _connections.get(node)
    if existing and existing.connected:
        return existing
    _connections.pop(node, None)

    try:
        if node not in settings.FREESWITCH_NODES:
            logger.error(f"FreeSWITCH node '{node}' not configured")
            return None

        cfg = settings.FREESWITCH_NODES[node]
        client = ESLClient(
            host=cfg['host'],
            port=int(cfg['port']),
            password=cfg['password'],
        )
        client.connect()
        _connections[node] = client
        logger.info(f"Connected to FreeSWITCH node '{node}' at {cfg['host']}:{cfg['port']}")
        return client

    except Exception as exc:
        logger.error(f"Error connecting to FreeSWITCH node '{node}': {exc}")
        return None


def find_dialer_node(callrequest_id: int) -> str:
    """Load-balance a callrequest across FreeSWITCH nodes by modulo."""
    nodes = list(settings.FREESWITCH_NODES.keys())
    if not nodes:
        logger.error("No FreeSWITCH nodes configured")
        return 'fs1'
    return nodes[callrequest_id % len(nodes)]


def dial_out(command: str, callrequest_id: int) -> str:
    """
    Send a bgapi originate command to FreeSWITCH.

    Returns the Job-UUID on success, or 'error' on failure.
    """
    node = find_dialer_node(callrequest_id)
    try:
        conn = get_esl_connection(node)
        if not conn:
            logger.error(f"No ESL connection available for node '{node}'")
            return 'error'

        response = conn.send(command)
        job_uuid = _extract_job_uuid(response)

        if job_uuid != 'error':
            logger.info(
                f"Dialed via node='{node}' job_uuid='{job_uuid}' "
                f"callrequest_id={callrequest_id}"
            )
        else:
            logger.error(f"Failed to extract Job-UUID. Reply: {response.headers}")
        return job_uuid

    except Exception as exc:
        logger.error(f"ESL dial_out error on node '{node}': {exc}")
        # Drop the (possibly broken) cached connection so the next call reconnects
        _connections.pop(node, None)
        return 'error'


def _extract_job_uuid(response) -> str:
    """Extract the Job-UUID from an ESL bgapi reply (header or Reply-Text)."""
    headers = getattr(response, 'headers', {})
    if isinstance(headers, dict):
        uuid = headers.get('Job-UUID', '').strip()
        if uuid:
            return uuid
        reply = headers.get('Reply-Text', '')
        if '+OK Job-UUID:' in reply:
            return reply.split('Job-UUID:', 1)[1].strip()

    # Plain string fallback
    if isinstance(response, str):
        for line in response.splitlines():
            if 'Job-UUID:' in line:
                return line.split('Job-UUID:', 1)[1].strip()

    return 'error'


def close_all_connections():
    """Close all ESL connections. Called on shutdown."""
    for node, conn in list(_connections.items()):
        try:
            conn.close()
            logger.info(f"Closed ESL connection to node '{node}'")
        except Exception as exc:
            logger.error(f"Error closing ESL connection to '{node}': {exc}")
    _connections.clear()
