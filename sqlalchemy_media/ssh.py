
import logging
import os
from os.path import join

import paramiko
from paramiko.config import SSHConfig, SSH_PORT

from sqlalchemy_media.exceptions import SSHError
from sqlalchemy_media.optionals import ensure_paramiko

ensure_paramiko()
logger = logging.getLogger('ssh')
logger.addHandler(logging.NullHandler())


class SSHClient(paramiko.SSHClient):
    config = SSHConfig()
    _sftp_client = None

    def __init__(self):
        super().__init__()
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def load_config_file(self, filename=None):
        filename = filename or self.config_file
        with open(filename) as f:
            self.config.parse(f)

    @property
    def config_file(self):
        return '%s/config' % self.config_directory

    @property
    def config_directory(self):
        return '%s/.ssh' % os.environ['HOME']

    @property
    def sftp(self):
        return self._sftp_client

    def connect(
            self,
            hostname,
            port=SSH_PORT,
            username=None,
            password=None,
            pkey=None,
            key_filename=None,
            timeout=None,
            allow_agent=True,
            look_for_keys=True,
            compress=False,
            sock=None,
            gss_auth=False,
            gss_kex=False,
            gss_deleg_creds=True,
            gss_host=None,
            banner_timeout=None):
        options = self.config.lookup(hostname)

        identity_file = options.get('identityfile', [key_filename])
        if identity_file:
            identity_file = identity_file[0]
        if identity_file and not identity_file.startswith('/'):
            identity_file = join(self.config_directory, identity_file)

        port = int(options.get('port', port))

        super().connect(
            hostname=options.get('hostname', hostname),
            port=port,
            username=options.get('user', username),
            password=options.get('password', password),
            pkey=pkey,
            key_filename=identity_file,
            timeout=options.get('connecttimeout', timeout),
            allow_agent=allow_agent,
            look_for_keys=look_for_keys,
            compress=compress,
            sock=sock,
            gss_auth=gss_auth,
            gss_kex=gss_kex,
            gss_deleg_creds=gss_deleg_creds,
            gss_host=gss_host,
            banner_timeout=banner_timeout
        )

        self._sftp_client = self.open_sftp()

    def remove(self, filename):
        stdin, stdout, stderr = self.exec_command(b'rm "%s"' % filename.encode())
        err = stderr.read()
        if err:
            raise SSHError('Cannot remove %s\nDetails: %s' % (filename, err))
