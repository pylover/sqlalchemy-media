from sqlalchemy_media.context import get_id as get_context_id
from sqlalchemy_media.stores.exceptions import ContextError, DefaultStoreError


# Global variable to store contexts
_context_stacks = {}

# global variable to store store factories
_factories = {}


class StoreManager(object):

    _stores = None
    _default = None

    def __enter__(self):
        _context_stacks.setdefault(get_context_id(), []).append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _context_stacks.setdefault(get_context_id(), []).pop()
        self.cleanup()

    @property
    def stores(self):
        if self._stores is None:
            self._stores = {}
        return self._stores

    @classmethod
    def get_current_store_manager(cls) -> 'StoreManager':
        try:
            return _context_stacks.setdefault(get_context_id(), [])[-1]
        except IndexError:
            raise ContextError('Not in store manager context.')

    def cleanup(self):
        for store in self.stores.values():
            store.cleanup()
        self.stores.clear()

    @classmethod
    def make_default(cls, key):
        cls._default = key

    @classmethod
    def register(cls, key, store_factory, default=False):
        _factories[key] = store_factory
        if default:
            cls._default = key

    @classmethod
    def unregister(cls, key):
        if key == cls._default:
            cls._default = None

        if key in _factories:
            del _factories[key]

    def get(self, key=None):
        if key is None:
            if self._default is None:
                raise DefaultStoreError()
            key = self._default

        if key not in self.stores:
            factory = _factories[key]
            self.stores[key] = factory()
        return self.stores[key]

    @property
    def default_store(self):
        return self.get()
