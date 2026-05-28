"""
FreeSWITCH ESL integration using greenswitch.
Replaces the old python-ESL blocking library with async greenswitch.
"""
from __future__ import annotations
import logging
from typing import Optional
from django.conf import settings
import greenswitch

logger = logging.getLogger(__name__)

# Connection pool - one connection per FS node
_connections: dict[str, greenswitch.InboundESL] = {}


def get_esl_connection(node: str = 'fs1') -> Optional[greenswitch.InboundESL]:
    """
    Get or create an ESL connection for the given FreeSWITCH node.
    Connections are cached and reused.
    
    Args:
        node: FreeSWITCH node identifier from settings.FREESWITCH_NODES
        
    Returns:
        greenswitch.InboundESL connection or None on error
    """
    if node not in _connections:
        try:
            if node not in settings.FREESWITCH_NODES:
                logger.error(f"FreeSWITCH node '{node}' not configured")
                return None
            
            cfg = settings.FREESWITCH_NODES[node]
            
            conn = greenswitch.InboundESL(
                host=cfg['host'],
                port=cfg['port'],
                password=cfg['password'],
            )
            conn.connect()
            
            if not conn.connected:
                logger.error(f"Failed to connect to FreeSWITCH node '{node}'")
                return None
            
            _connections[node] = conn
            logger.info(f"Connected to FreeSWITCH node '{node}' at {cfg['host']}:{cfg['port']}")
            
        except Exception as exc:
            logger.error(f"Error connecting to FreeSWITCH node '{node}': {exc}")
            return None
    
    return _connections.get(node)


def find_dialer_node(callrequest_id: int) -> str:
    """
    Load-balance callrequest across FreeSWITCH nodes.
    Uses modulo to distribute calls evenly.
    
    Args:
        callrequest_id: Callrequest primary key
        
    Returns:
        Node name from settings.FREESWITCH_NODES keys
    """
    nodes = list(settings.FREESWITCH_NODES.keys())
    if not nodes:
        logger.error("No FreeSWITCH nodes configured")
        return 'fs1'  # Default fallback
    
    # Simple round-robin based on callrequest ID
    node_index = callrequest_id % len(nodes)
    return nodes[node_index]


def dial_out(command: str, callrequest_id: int) -> str:
    """
    Send bgapi originate command to FreeSWITCH.
    
    Args:
        command: Full FreeSWITCH command (e.g., "bgapi originate ...")
        callrequest_id: Callrequest ID for load balancing
        
    Returns:
        Job-UUID on success, 'error' on failure
    """
    node = find_dialer_node(callrequest_id)
    
    try:
        conn = get_esl_connection(node)
        if not conn:
            logger.error(f"No ESL connection available for node '{node}'")
            return 'error'
        
        # Send command
        response = conn.send(command)
        
        if not response:
            logger.error(f"No response from FreeSWITCH node '{node}'")
            return 'error'
        
        # Extract Job-UUID from response
        job_uuid = _extract_job_uuid(str(response))
        
        if job_uuid != 'error':
            logger.info(
                f"Dialed via node='{node}' job_uuid='{job_uuid}' "
                f"callrequest_id={callrequest_id}"
            )
        else:
            logger.error(f"Failed to extract Job-UUID from response: {response}")
        
        return job_uuid
        
    except Exception as exc:
        logger.error(f"ESL dial_out error on node '{node}': {exc}")
        return 'error'


def _extract_job_uuid(response: str) -> str:
    """
    Extract Job-UUID from FreeSWITCH bgapi response.
    
    Args:
        response: ESL response string
        
    Returns:
        Job-UUID or 'error' if not found
    """
    for line in response.splitlines():
        line = line.strip()
        if line.startswith('Job-UUID:'):
            # Format: "Job-UUID: xxxxx-xxxx-xxxx-xxxx-xxxxxx"
            parts = line.split(':', 1)
            if len(parts) == 2:
                return parts[1].strip()
    
    # Alternative: look for +OK followed by UUID
    lines = response.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == '+OK' and i + 1 < len(lines):
            # Next line might be the Job-UUID
            potential_uuid = lines[i + 1].strip()
            if len(potential_uuid) > 20:  # UUIDs are long
                return potential_uuid
    
    return 'error'


def close_all_connections():
    """Close all ESL connections. Called on shutdown."""
    for node, conn in _connections.items():
        try:
            conn.stop()
            logger.info(f"Closed ESL connection to node '{node}'")
        except Exception as exc:
            logger.error(f"Error closing ESL connection to '{node}': {exc}")
    
    _connections.clear()
