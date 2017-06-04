
import unittest
from os.path import dirname, join, abspath, split, exists
from os import mkdir

import paramiko
import mockssh
from mockssh.server import SERVER_KEY_PATH

from sqlalchemy_media.ssh import SSHClient


class MockupSSHServer(mockssh.Server):

    def client(self, uid):
        private_key_path, _ = self._users[uid]
        c = SSHClient()
        host_keys = c.get_host_keys()
        key = paramiko.RSAKey.from_private_key_file(SERVER_KEY_PATH)
        host_keys.add(self.host, "ssh-rsa", key)
        host_keys.add("[%s]:%d" % (self.host, self.port), "ssh-rsa", key)
        c.set_missing_host_key_policy(paramiko.RejectPolicy())
        c.connect(hostname=self.host,
                  port=self.port,
                  username=uid,
                  key_filename=private_key_path,
                  allow_agent=False,
                  look_for_keys=False)
        return c


class STFPClientTestCase(unittest.TestCase):

    def setUp(self):
        self.here = abspath(dirname(__file__))
        self.tempdir = join(self.here, 'temp')
        if not exists(self.tempdir):
            mkdir(self.tempdir)

        self.users = {
            'test': join(self.here, 'stuff', 'test-id_rsa')
        }
        self.server = MockupSSHServer(self.users)
        self.server.__enter__()

    def tearDown(self):
        self.server.__exit__()

    def test_connectivity(self):
        client = self.server.client('test')
        stdin, stdout, stderr = client.exec_command('ls')
        self.assertIn(split(__file__)[1],  stdout.read().decode())

    def test_put_file(self):
        client = self.server.client('test')
        expected_content = 'TEST text'

        try:
            f = client.sftp.file('temp/a.txt', mode='w')
            f.write(expected_content.encode())
            f.close()

        finally:
            client.sftp.close()

        with open(join(self.tempdir, 'a.txt'), encoding='utf8') as f:
            content = f.read()

        self.assertEqual(content, expected_content)










