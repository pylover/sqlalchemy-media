

from cherrypy import expose
from sqlalchemy_media import StoreManager

from cp_sam.models import DBSession, Person


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


class Root(object):

    @expose
    def index(self):
        page = MasterPageView('Index')
        page += '<form method="POST" action="submit" enctype="multipart/form-data">'
        page += '<input type="text" name="name" value="Your Name here"/>'
        page += '<input type="file" name="avatar" />'
        page += '<input type="submit" />'
        page += '</form>'
        return page

    @expose
    def submit(self, name=None, avatar=None):
        session = DBSession()

        with StoreManager(session):
            new_person = Person(name=name, avatar=avatar.file if avatar else avatar)
            session.add(new_person)
            session.commit()

            page = MasterPageView('View', body='<ul>')
            for p in session.query(Person):
                page += '<li>'
                page += '<img src="%s" alt="%s">' % (p.avatar.locate(), p.name)
                page += '<h2>%s</h2>' % p.name
                page += '<h2>ID: %s</h2>' % p.id
                page += '</li>'

            page += '</ul>'
            return page
