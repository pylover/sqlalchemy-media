
import json
import functools
from os import path, mkdir, getcwd

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import TypeDecorator, Unicode
from sqlalchemy_media import Image, ImageValidator, ImageProcessor, ImageAnalyzer, StoreManager, \
    FileSystemStore
from sqlalchemy_media.constants import MB, KB


WORKING_DIR = path.abspath(getcwd())
TEMP_PATH = path.join(WORKING_DIR, 'static', 'avatars')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demo.db'
db = SQLAlchemy(app)


StoreManager.register(
    'fs',
    functools.partial(FileSystemStore, TEMP_PATH, 'http://localhost:5000/static/avatars'),
    default=True
)


class MasterPageView(object):
    header = '<!DOCTYPE html><head><meta charset="utf-8"><title>%s</title></head><body>'
    footer = '</body>'

    def __init__(self, title='demo', body=''):
        self.title = title
        self.body = body

    def __str__(self):
        return (self.header % self.title) + self.body + self.footer

    def __iadd__(self, other):
        self.body += other if isinstance(other, str) else str(other)
        return self

    def __iter__(self):
        return iter(str(self).splitlines())


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
        ImageAnalyzer(),
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


class Person(db.Model):
    __tablename__ = 'person'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(Unicode)
    avatar = db.Column(Avatar.as_mutable(Json))


@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(exception)
    return "500"


@app.route("/", methods=['GET', 'POST'])
def index():

    page = MasterPageView('Index')
    page += '<form method="POST" action="/" enctype="multipart/form-data">'
    page += '<input type="text" name="name" value="Your Name here"/>'
    page += '<input type="file" name="avatar" />'
    page += '<input type="submit" />'
    page += '</form>'
    page += '<hr />'

    with StoreManager(db.session()):
        if request.method == 'POST':

            new_person = Person(name=request.form['name'], avatar=request.files['avatar'])
            db.session.add(new_person)
            db.session.commit()

        page += '<ul>'
        for p in db.session.query(Person):
            page += '<li>'
            page += '<img src="%s" alt="%s">' % (p.avatar.locate(), p.name)
            page += '<h2>%s</h2>' % p.name
            page += '<h2>ID: %s</h2>' % p.id
            page += '</li>'
        page += '</ul>'

    return str(page)


if __name__ == "__main__":
    if not path.exists(TEMP_PATH):
        mkdir(TEMP_PATH)
    db.create_all()
    app.run()
