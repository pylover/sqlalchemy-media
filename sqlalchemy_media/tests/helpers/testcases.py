import unittest
import functools
import shutil
from os import makedirs
from os.path import join, dirname, abspath, exists

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_media import StoreManager, FileSystemStore


class SqlAlchemyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_uri = 'sqlite:///:memory:'

    def setUp(self):
        self.Base = declarative_base()
        self.engine = create_engine(self.db_uri, echo=False)

    def create_all_and_get_session(self):
        self.Base.metadata.create_all(self.engine, checkfirst=True)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=True,
            twophase=False
        )
        return self.session_factory()


class TempStoreTestCase(SqlAlchemyTestCase):
    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(join(dirname(__file__), '..'))
        cls.stuff_path = join(cls.this_dir, 'stuff')

        # Pointing to some handy files.
        cls.dog_jpeg = join(cls.stuff_path, 'dog.jpg')
        cls.cat_jpeg = join(cls.stuff_path, 'cat.jpg')
        cls.dog_png = join(cls.stuff_path, 'dog.png')
        cls.cat_png = join(cls.stuff_path, 'cat.png')

        super().setUpClass()

    def setUp(self):
        self.temp_path = join(self.this_dir, 'temp', self.__class__.__name__, self._testMethodName)
        self.sys_temp_path = join('/tmp/sa-media-tests', self.__class__.__name__, self._testMethodName)
        self.base_url = 'http://static1.example.orm'

        # Remove previous files, if any! to make a clean temp directory:
        if exists(self.temp_path):  # pragma: no cover
            shutil.rmtree(self.temp_path)

        makedirs(self.temp_path)

        StoreManager.register('fs', functools.partial(FileSystemStore, self.temp_path, self.base_url), default=True)
        StoreManager.register(
            'temp_fs',
            functools.partial(FileSystemStore, self.sys_temp_path, self.base_url)
        )
        super().setUp()
