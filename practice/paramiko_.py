import os
from os.path import join, dirname

import paramiko
from paramiko.config import SSHConfig, SSH_PORT

CONFIG_FILE_NAME = '%s/.ssh/config' % os.environ['HOME']


class SSHClient(paramiko.SSHClient):
    config = SSHConfig()

    @classmethod
    def load_config_file(cls, filename):
        with open(filename) as f:
            cls.config.parse(f)

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

        identity_file = options.get('identityfile')
        if identity_file and not identity_file.startswith('/'):
            identity_file = join(dirname(CONFIG_FILE_NAME), identity_file)

        return super().connect(
            hostname=options.get('hostname', hostname),
            port=int(options.get('port', port)),
            username=options.get('user', username),
            password=options.get('password', password),
            key_filename=identity_file
        )


if __name__ == '__main__':
    ssh = SSHClient()
    ssh.load_config_file(CONFIG_FILE_NAME)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('carrene-new')
    stdin, stdout, stderr = ssh.exec_command('ls')
    print(stdout.read().decode())
