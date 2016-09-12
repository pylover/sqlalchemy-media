
from sqlalchemy_media.stores.base import Store
from sqlalchemy_media.stores.exceptions import ContextError


# noinspection PyAbstractClass
class LocalProxyStore(Store):
    """
    Proxy of another image storage.

    :param get_current_object: a function that returns "current" store
    :type get_current_object: :class:`collections.Callable`
    """

    def __init__(self, get_current_object):
        if not callable(get_current_object):
            raise TypeError('expected callable')
        object.__setattr__(self, 'get_current_object', get_current_object)

    def __getattr__(self, key):
        return getattr(object.__getattribute__(self, 'get_current_object')(), key)

    def __setattr__(self, key, value):
        return setattr(object.__getattribute__(self, 'get_current_object')(), key, value)

    def __delattr__(self, key):
        return delattr(object.__getattribute__(self, 'get_current_object')(), key)

    def __eq__(self, other):
        return object.__getattribute__(self, 'get_current_object')() == other

    def __ne__(self, other):
        return object.__getattribute__(self, 'get_current_object')() != other

    def __hash__(self):
        return hash(object.__getattribute__(self, 'get_current_object')())

    def __repr__(self):
        try:
            _current_store = object.__getattribute__(self, 'get_current_object')()
        except ContextError:
            return '<Unbound {0}.{1}>'.format(self.__module__, self.__name__)
        return 'Proxied: %s' % repr(_current_store)

