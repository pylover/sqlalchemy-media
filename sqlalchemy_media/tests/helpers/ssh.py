import shutil
from os import makedirs
from os.path import join, dirname, abspath, exists

import paramiko
import mockssh
from mockssh.server import SERVER_KEY_PATH

from sqlalchemy_media.ssh import SSHClient
from .testcases import SqlAlchemyTestCase


class MockupSSHServer(mockssh.Server):
    def client(self, uid):
        private_key_path, _ = self._users[uid]
        client = SSHClient()
        host_keys = client.get_host_keys()
        key = paramiko.RSAKey.from_private_key_file(SERVER_KEY_PATH)
        host_keys.add(self.host, "ssh-rsa", key)
        host_keys.add("[%s]:%d" % (self.host, self.port), "ssh-rsa", key)
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(
            hostname=self.host,
            port=self.port,
            username=uid,
            key_filename=private_key_path,
            allow_agent=False,
            look_for_keys=False
        )
        return client


class MockupSSHTestCase(SqlAlchemyTestCase):
    def setUp(self):
        self.here = abspath(join(dirname(__file__), '..'))
        self.relative_temp_path = join('temp', self.__class__.__name__, self._testMethodName)
        self.temp_path = join(self.here, self.relative_temp_path)
        # Remove previous files, if any! to make a clean temp directory:
        if exists(self.temp_path):  # pragma: no cover
            shutil.rmtree(self.temp_path)

        makedirs(self.temp_path)

        self.users = {
            'test': join(self.here, 'stuff', 'test-id_rsa')
        }
        self.server = MockupSSHServer(self.users)
        self.server.__enter__()

    def create_ssh_client(self):
        client = self.server.client('test')
        return client

    def tearDown(self):
        self.server.__exit__()
