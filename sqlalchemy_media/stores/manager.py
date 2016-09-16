from typing import Iterable

from sqlalchemy import event

from sqlalchemy_media.context import get_id as get_context_id
from sqlalchemy_media.stores.exceptions import ContextError, DefaultStoreError

# Global variable to store contexts
_context_stacks = {}

# global variable to store store factories
_factories = {}

# global variable to store observing attributes
_observing_attributes = set()


class StoreManager(object):

    _stores = None
    _default = None
    _files_to_delete_after_commit = None
    _files_to_delete_after_rollback = None

    def __init__(self, session):
        self.session = session
        self.reset_files_state()

    def __enter__(self):
        self.bind_events()
        _context_stacks.setdefault(get_context_id(), []).append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _context_stacks.setdefault(get_context_id(), []).pop()
        self.unbind_events()
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

    def bind_events(self):
        event.listen(self.session, 'after_commit', self.on_commit)
        event.listen(self.session, 'after_soft_rollback', self.on_rollback)
        event.listen(self.session, 'persistent_to_deleted', self.on_delete)

    def unbind_events(self):
        event.remove(self.session, 'after_commit', self.on_commit)
        event.remove(self.session, 'after_soft_rollback', self.on_rollback)
        event.remove(self.session, 'persistent_to_deleted', self.on_delete)

    def register_to_delete_after_commit(self, *files: Iterable['Attachment']):
        self._files_to_delete_after_commit.extend(files)

    def register_to_delete_after_rollback(self, *files: Iterable['Attachment']):
        self._files_to_delete_after_rollback.extend(files)

    def reset_files_state(self):
        self._files_to_delete_after_commit = []
        self._files_to_delete_after_rollback = []

    def on_commit(self, session):
        for f in self._files_to_delete_after_commit:
            f.delete()
        self.reset_files_state()

    def on_rollback(self, session, transaction):
        for f in self._files_to_delete_after_rollback:
            f.delete()
        self.reset_files_state()

    def on_delete(self, session, instance):
        for attribute in _observing_attributes:
            if isinstance(instance, attribute.class_):
                self.register_to_delete_after_commit(getattr(instance, attribute.key).copy())

    @staticmethod
    def observe_attribute(attr):
        if attr not in _observing_attributes:
            _observing_attributes.add(attr)

            def set(target, value, old_value, initiator):
                if old_value is None:
                    return

                if value is None:
                    store_manager = StoreManager.get_current_store_manager()
                    store_manager.register_to_delete_after_commit(getattr(target, attr.key).copy())

            event.listen(attr, 'set', set, propagate=True)
