from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_media import File, MagicAnalyzer, ContentTypeValidator


TEMP_PATH = '/tmp/sqlalchemy-media'
Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=False)


class PDFFile(File):
    __analyzer__ = MagicAnalyzer()
    __validate__ = ContentTypeValidator(['application/pdf', 'image/jpeg'])
