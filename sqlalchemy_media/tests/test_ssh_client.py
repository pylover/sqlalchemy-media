
import unittest
from os.path import join, exists


from sqlalchemy_media.tests.helpers import MockupSSHTestCase


class SSHClientTestCase(MockupSSHTestCase):

    def test_connectivity(self):
        client = self.create_ssh_client()
        stdin, stdout, stderr = client.exec_command('ls')
        self.assertTrue(len(stdout.read()) > 0)

    def test_put_delete_open_file(self):
        client = self.create_ssh_client()
        expected_content = 'TEST text'

        try:
            filename = join(self.temp_path, 'a.txt')

            # Putting
            f = client.sftp.file(filename, mode='w')
            f.write(expected_content.encode())
            f.close()

            # Opening the file directly using os
            with open(filename, encoding='utf8') as f:
                content = f.read()
            self.assertEqual(content, expected_content)

            # Opening via ssh client
            with client.sftp.open(filename) as f:
                content = f.read().decode()
            self.assertEqual(content, expected_content)

            # Deleting
            client.remove(filename)
            self.assertFalse(exists(filename))

        finally:
            client.sftp.close()


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
