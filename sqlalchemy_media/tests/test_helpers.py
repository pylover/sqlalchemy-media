import unittest

from sqlalchemy_media.helpers import is_uri


class HelpersTestCase(unittest.TestCase):

    def test_is_uri(self):
        self.assertTrue(is_uri('http://path/to?342=324322&param'))
        self.assertTrue(is_uri('ftp://path/to?342=324322&param'))
        self.assertTrue(is_uri('tcp://path/to?342=324322&param'))
        self.assertTrue(is_uri('protocol://path/to?342=324322&param'))
        self.assertFalse(is_uri('http:/path/to?342=324322&param'))
        self.assertFalse(is_uri('path/to?342=324322&param'))
        self.assertFalse(is_uri('/path/to?342=324322&param'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
