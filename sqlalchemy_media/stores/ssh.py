from os.path import join, dirname

from sqlalchemy_media.optionals import ensure_paramiko
from sqlalchemy_media.typing_ import FileLike
from .base import Store


class SSHStore(Store):
    """
    Store for SSH protocol. aka SFTP

    .. versionadded:: 0.12.0

    :param hostname: The ssh server's hostname to connect to. It will be looked-up from ssh config file to find
                     another options if given.
                     An instance of the :class:`paramiko.SSHClient` may be passed instead of the hostname.
    :param root_path: The path to a directory on the ssh server to store files.
    :param base_url: The base url path to include at the beginning of the file's path to yield the access url.
    :param ssh_config_file: The standard ssh config file. is not given, the file `$HOME/.ssh/config` will be tried.
    :param kwargs: Additional keyword arguments to pass to the :class:`paramiko.SSHClient`
    """

    def __init__(self, hostname, root_path, base_url, ssh_config_file=None, **kwargs):
        ensure_paramiko()
        from sqlalchemy_media.ssh import SSHClient

        self.root_path = root_path
        self.base_url = base_url.rstrip('/')
        if isinstance(hostname, SSHClient):
            self.ssh_client = hostname
        else:
            self.ssh_client = SSHClient()
            self.ssh_client.load_config_file(filename=ssh_config_file)
            self.ssh_client.connect(hostname, **kwargs)

        self.ssh_client.sftp.chdir(None)

    def _get_remote_path(self, filename):
        return join(self.root_path, filename)

    def put(self, filename: str, stream: FileLike) -> int:
        remote_filename = self._get_remote_path(filename)
        remote_directory = dirname(remote_filename)
        self.ssh_client.exec_command(b'mkdir -p "%s"' % remote_directory.encode())
        result = self.ssh_client.sftp.putfo(stream, remote_filename)
        return result.st_size

    def delete(self, filename: str) -> None:
        remote_filename = self._get_remote_path(filename)
        self.ssh_client.remove(remote_filename)

    def open(self, filename: str, mode: str='rb'):
        remote_filename = self._get_remote_path(filename)
        return self.ssh_client.sftp.open(remote_filename, mode=mode)

    def locate(self, attachment) -> str:
        return '%s/%s' % (self.base_url, attachment.path)
