import functools
import shutil
import unittest
from os import makedirs
from os.path import join, dirname, abspath, exists

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy_media import StoreManager, FileSystemStore

from .config import TEST_BUCKET
from .s3 import mockup_s3_server, create_s3_store


class SqlAlchemyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_uri = 'sqlite:///:memory:'

    def setUp(self):
        self.Base = declarative_base()
        self.engine = create_engine(self.db_uri, echo=False)

    def create_all_and_get_session(self, expire_on_commit: bool = False):
        """
        A factory method for making a SQLAlchemy session factory object.
        :param expire_on_commit: @see: https://docs.sqlalchemy.org/en/14/orm/session_api.html?highlight=expire_on_commit#sqlalchemy.orm.Session.params.expire_on_commit
        """
        self.Base.metadata.create_all(self.engine, checkfirst=True)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=expire_on_commit,
            twophase=False
        )
        return self.session_factory()


class S3TestCase(unittest.TestCase):
    """Mixin for runnning the S3 server"""

    def run(self, result):
        with mockup_s3_server(bucket=TEST_BUCKET) as (server, bucket_uri):
            self.storage = create_s3_store(
                bucket=TEST_BUCKET, base_url=bucket_uri
            )
            self.bucket_name = TEST_BUCKET
            self.server = server
            self.base_url = bucket_uri
            super(S3TestCase, self).run(result)


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
        self.temp_path = join(self.this_dir, 'temp', self.__class__.__name__,
                              self._testMethodName)
        self.sys_temp_path = join(
            '/tmp/sa-media-tests',
            self.__class__.__name__,
            self._testMethodName
        )
        self.base_url = 'http://localhost:9000'

        # Remove previous files, if any! to make a clean temp directory:
        if exists(self.temp_path):  # pragma: no cover
            shutil.rmtree(self.temp_path)

        makedirs(self.temp_path)

        StoreManager.register(
            'fs',
            functools.partial(FileSystemStore, self.temp_path, self.base_url),
            default=True
        )
        StoreManager.register(
            'temp_fs',
            functools.partial(
                FileSystemStore,
                self.sys_temp_path,
                self.base_url
            )
        )
        super().setUp()
