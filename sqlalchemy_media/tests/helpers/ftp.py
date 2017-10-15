import os
import ftplib
from collections import deque


# noinspection PyMethodMayBeStatic
# noinspection PyUnusedLocal
# noinspection PyMissingConstructor
# noinspection PyMethodOverriding
class MockFTP(ftplib.FTP):  # pragma: nocover
    """ Mock FTP lib for testing """

    def __init__(self):
        self._files = None
        self._size = 0
        self._dirlist = None
        self._exists = True
        self._stack = deque()
        self._contents = ''

    def storbinary(self, command, f):
        f.seek(0, os.SEEK_END)
        self._size = f.tell()

    def retrbinary(self, command, callback):
        callback(self._contents)
        return

    def pwd(self):
        return "/".join(self._stack)

    def nlst(self, dirname=None):
        return self._files

    def mkd(self, dirname):
        return

    def rmd(self, dirname):
        return

    def delete(self, filename):
        if not self._exists:
            raise Exception("Doesn't exist")
        return True

    def rename(self, fromname, toname):
        return

    def cwd(self, pathname):
        if not self._exists:
            self._exists = True
            raise Exception("Doesn't exist")
        for dir_ in pathname.split("/"):
            if dir_ == '..':
                self._stack.pop()
            else:
                self._stack.append(dir_)

    def size(self, filename):
        return self._size

    def dir(self, dirname, callback):
        for line in self._dirlist.splitlines():
            callback(line)

    def sendcmd(self, command):
        return command

    def set_pasv(self, passive):
        return passive

    def quit(self):
        raise Exception('Fake a a problem with quit')

    def close(self):
        return True

    def _set_files(self, files):
        self._files = files

    def _set_dirlist(self, dirlist):
        self._dirlist = dirlist

    def _set_exists(self, exists):
        self._exists = exists

    def _set_contents(self, contents):
        self._contents = contents
