import os
import tempfile
from dataclasses import dataclass

from django.conf import settings


@dataclass
class ExtensionSyncResult:
    success: bool
    xml_written: bool = False
    reloaded: bool = False
    message: str = ''
    xml_path: str = ''
    status_code: int = 200

    def as_dict(self):
        return {
            'success': self.success,
            'xml_written': self.xml_written,
            'reloaded': self.reloaded,
            'message': self.message,
            'xml_path': self.xml_path,
        }


def sync_agent_extension(agent) -> ExtensionSyncResult:
    """Write an agent's FreeSWITCH directory XML and reload FreeSWITCH XML."""
    if not agent.sip_extension:
        return ExtensionSyncResult(False, message='Extension number not set.', status_code=400)
    if not agent.sip_password:
        return ExtensionSyncResult(False, message='SIP password not set.', status_code=400)

    dir_path = getattr(settings, 'FS_DIRECTORY_DIR', '/etc/freeswitch/directory/default')
    xml_path = os.path.join(dir_path, f'{agent.sip_extension}.xml')

    tmp_path = ''
    try:
        os.makedirs(dir_path, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode='w',
            newline='\n',
            dir=dir_path,
            prefix=f'.{agent.sip_extension}.',
            suffix='.tmp',
            delete=False,
        ) as fh:
            tmp_path = fh.name
            fh.write(agent.generate_fs_directory_xml())
        os.replace(tmp_path, xml_path)
    except (IOError, OSError) as exc:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return ExtensionSyncResult(
            False,
            message=f'Cannot write to {xml_path}: {exc}',
            xml_path=xml_path,
            status_code=500,
        )

    try:
        from apps.dialer_cdr.esl import get_esl_connection

        conn = get_esl_connection('fs1')
        if conn:
            conn.send('api reloadxml')
            return ExtensionSyncResult(
                True,
                xml_written=True,
                reloaded=True,
                message=f'Extension {agent.sip_extension} synced to FreeSWITCH.',
                xml_path=xml_path,
            )
    except Exception:
        pass

    return ExtensionSyncResult(
        True,
        xml_written=True,
        reloaded=False,
        message=f'XML written to {xml_path}. Run "reloadxml" in FreeSWITCH CLI to activate.',
        xml_path=xml_path,
    )
