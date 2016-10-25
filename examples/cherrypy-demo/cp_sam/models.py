
import json

from sqlalchemy import TypeDecorator, Unicode, Column, Integer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_media import Image, ImageValidator, ImageProcessor, WandAnalyzer
from sqlalchemy_media.constants import MB, KB


Base = declarative_base()
engine = create_engine('sqlite:///demo.db', echo=True)
DBSession = scoped_session(sessionmaker(bind=engine))


class Json(TypeDecorator):
    impl = Unicode

    def process_bind_param(self, value, engine):
        return json.dumps(value)

    def process_result_value(self, value, engine):
        if value is None:
            return None
        return json.loads(value)


class Avatar(Image):
    __auto_coercion__ = True
    __pre_processors__ = [
        WandAnalyzer(),
        ImageValidator(
            minimum=(10, 10),
            maximum=(3840, 3840),
            content_types=('image/jpeg', 'image/png', 'image/gif'),
            min_aspect_ratio=1,
            max_aspect_ratio=1
        ),
        ImageProcessor(fmt='jpeg', width=128)
    ]
    __max_length__ = 6*MB
    __min_length__ = 10*KB


class Person(Base):
    __tablename__ = 'person'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    avatar = Column(Avatar.as_mutable(Json))


Base.metadata.create_all(engine, checkfirst=True)

