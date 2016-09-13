
from sqlalchemy_media.stores.base import Store
from sqlalchemy_media.stores.exceptions import ContextError


# noinspection PyAbstractClass
class LocalProxyStore(Store):

    def __getattr__(self, key):
        return getattr(object.__getattribute__(self, 'get_current_store')(), key)

    def __setattr__(self, key, value):
        return setattr(object.__getattribute__(self, 'get_current_store')(), key, value)

    def __delattr__(self, key):
        return delattr(object.__getattribute__(self, 'get_current_store')(), key)

    def __eq__(self, other):
        return object.__getattribute__(self, 'get_current_store')() == other

    def __ne__(self, other):
        return object.__getattribute__(self, 'get_current_store')() != other

    def __hash__(self):
        return hash(object.__getattribute__(self, 'get_current_store')())

    def __repr__(self):
        try:
            _current_store = object.__getattribute__(self, 'get_current_store')()
        except ContextError:
            return '<Unbound {0}.{1}>'.format(self.__module__, self.__name__)
        return 'Proxied: %s' % repr(_current_store)
