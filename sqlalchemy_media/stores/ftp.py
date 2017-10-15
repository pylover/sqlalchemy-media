from os.path import join, dirname, basename
from io import BytesIO
from sqlalchemy_media.typing_ import FileLike
from .base import Store
from ftplib import FTP, FTP_TLS


class FTPStore(Store):
    """
    Store for FTP protocol.

    .. versionadded:: 0.16.0
    :param hostname: FTP server hostname or instance of :class:`ftplib.FTP`. 
                     Note if pass the instance of :class:`ftplib.FTP` do not need to
                     set `username`, `password`, `passive`, `secure`, `kwargs` arguments.
    :param root_path: Root working directory path on FTP server.
    :param base_url: First part of URL that using to locate file access URL. 
    :param username: FTP server username.
    :param password: FTP server password.
    :param passive: Enable passive FTP mode. 
                    (How it works? https://www.ietf.org/rfc/rfc959.txt, http://slacksite.com/other/ftp.html)
    :param secure: Enable secure TLS connection.
    :param kwargs: Additional arguments to FTP client 
                   (for :class:`ftplib.FTP` or :class:`ftplib.FTP_TLS` based on `secure` argument status) 
    """

    def __init__(self, hostname, root_path, base_url,
                 username=None, password=None, passive=True, secure=False, **kwargs):

        if isinstance(hostname, FTP):
            self.ftp_client = hostname

        else:  # pragma: nocover
            if secure:
                self.ftp_client = FTP_TLS(host=hostname, user=username, passwd=password, **kwargs)
                # noinspection PyUnresolvedReferences
                self.ftp_client.prot_p()

            else:
                self.ftp_client = FTP(host=hostname, user=username, passwd=password, **kwargs)

            self.ftp_client.set_pasv(passive)

        self.root_path = root_path
        self.base_url = base_url.rstrip('/')

    def _get_remote_path(self, filename):
        return join(self.root_path, filename)

    def _change_directory(self, remote):
        remote_dirs = remote.split('/')
        for directory in remote_dirs:
            # noinspection PyBroadException
            try:
                self.ftp_client.cwd(directory)
            except Exception:
                # Try to make directory if not exists
                self.ftp_client.mkd(directory)
                self.ftp_client.cwd(directory)

    def put(self, filename: str, stream: FileLike) -> int:
        remote_filename = self._get_remote_path(filename)
        remote_dir = dirname(remote_filename)
        remote_file = basename(remote_filename)
        current = self.ftp_client.pwd()
        self._change_directory(remote_dir)

        try:
            self.ftp_client.storbinary('STOR %s' % remote_file, stream)
            size = self.ftp_client.size(remote_file)
        finally:
            stream.close()
            self.ftp_client.cwd(current)
        return size

    def delete(self, filename: str) -> None:
        remote_filename = self._get_remote_path(filename)
        self.ftp_client.delete(remote_filename)

    def open(self, filename: str, mode: str='rb'):
        remote_filename = self._get_remote_path(filename)
        file_bytes = BytesIO()
        self.ftp_client.retrbinary("RETR %s" % remote_filename, file_bytes.write)
        file_bytes.seek(0)
        return file_bytes

    def locate(self, attachment) -> str:
        return '%s/%s' % (self.base_url, attachment.path)
