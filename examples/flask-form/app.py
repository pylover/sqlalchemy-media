import json
import functools
from os import path, mkdir, getcwd

from flask import Flask, g, redirect, render_template, url_for
from flask_wtf import CSRFProtect, FlaskForm
from flask_wtf.file import FileField, FileSize, FileAllowed, FileRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import TypeDecorator, Unicode
from sqlalchemy_media import (
    Image, ImageValidator, ImageProcessor, ImageAnalyzer,
    StoreManager, FileSystemStore,
)
from sqlalchemy_media.constants import MB, KB
from wtforms import fields


ROOT_PATH = path.abspath(getcwd())
TEMP_PATH = path.join(ROOT_PATH, 'static', 'avatars')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-sekret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
csrf = CSRFProtect(app)


StoreManager.register(
    'fs',
    functools.partial(FileSystemStore, TEMP_PATH, '/static/avatars'),
    default=True
)


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
            maximum=(4000, 4000),
            content_types=('image/jpeg', 'image/png', 'image/gif'),
            min_aspect_ratio=1,
            max_aspect_ratio=2,
        ),
        ImageProcessor(fmt='jpeg', width=128)
    ]
    __max_length__ = 6 * MB
    __min_length__ = 10 * KB


class Person(db.Model):
    __tablename__ = 'person'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(Unicode)
    avatar = db.Column(Avatar.as_mutable(Json))


class PersonForm(FlaskForm):
    name = fields.StringField(render_kw=dict(placeholder='Avatar Name (optional)'))
    avatar = FileField(validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif']),
        FileSize(min_size=10*KB, max_size=6*MB),
        FileRequired(),
    ])
    submit = fields.SubmitField('Submit')


@app.before_first_request
def setup_dev_env():
    if not path.exists(TEMP_PATH):
        mkdir(TEMP_PATH)
    db.create_all()


@app.before_request
def push_store_manager():
    g.store_manager = StoreManager.push_new(db.session, delete_orphan=True)


@app.after_request
def pop_store_manager(response):
    g.store_manager.pop()
    g.store_manager = None
    return response


@app.route("/", methods=['GET', 'POST'])
def index():
    form = PersonForm()
    if form.validate_on_submit():
        avatar = form.avatar.data
        person = Person(avatar=avatar,
                        name=form.name.data or avatar.filename)
        db.session.add(person)
        db.session.commit()
        return redirect(url_for('index'))

    people = db.session.query(Person).all()
    return render_template('index.html', form=form, people=people)


@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(exception)
    return "500"
