
import functools
from os import path, mkdir, getcwd

import cherrypy
from sqlalchemy_media import StoreManager, FileSystemStore

from .controllers import Root


__version__ = '0.1.0-dev.1'


WORKING_DIR = path.abspath(getcwd())
TEMP_PATH = path.join(WORKING_DIR, 'avatars')


def main():

    if not path.exists(TEMP_PATH):
        mkdir(TEMP_PATH)

    StoreManager.register(
        'fs',
        functools.partial(FileSystemStore, TEMP_PATH, 'http://localhost:8080/avatars'),
        default=True
    )

    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': WORKING_DIR
        },
        '/avatars': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': TEMP_PATH
        }
    }

    cherrypy.quickstart(Root(), config=conf)

