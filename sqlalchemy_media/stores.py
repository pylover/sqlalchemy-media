
from typing import Iterable
from os import makedirs, remove
from os.path import abspath, join, dirname, exists

from sqlalchemy import event
from sqlalchemy.util.langhelpers import symbol

from sqlalchemy_media.typing_ import Stream
from sqlalchemy_media.context import get_id as get_context_id
from sqlalchemy_media.exceptions import ContextError, DefaultStoreError
from sqlalchemy_media.helpers import copy_stream, open_stream


# Global variable to store contexts
_context_stacks = {}

# global variable to store store factories
_factories = {}

# global variable to store observing attributes
_observing_attributes = set()


class Store(object):
    """
    The abstract base class for all stores.
    """

    # noinspection PyMethodMayBeStatic
    def cleanup(self):
        """
        In derived class should cleanup all dirty stuff created while storing and deleting file.
        If not overridden, no error will be raised.

        .. seealso:: :meth:`.StoreManager.cleanup`

        """
        pass

    def put(self, filename: str, stream: Stream, *, min_length=None, max_length=None):
        """
        In driven class, should put the stream as the given filename in the store.

        :param filename:
        :param stream:
        :param min_length:
        :param max_length:
        :return:
        """
        raise NotImplementedError()

    def delete(self, filename: str):
        raise NotImplementedError()

    def open(self, filename: str, mode: str='r') -> Stream:
        raise NotImplementedError()

    def locate(self, attachment: 'Attachment') -> str:
        raise NotImplementedError()


class FileSystemStore(Store):

    def __init__(self, root_path: str, base_url: str, chunk_size: int=32768):
        self.root_path = abspath(root_path)
        self.base_url = base_url.rstrip('/')
        self.chunk_size = chunk_size

    def _get_physical_path(self, filename: str) -> str:
        return join(self.root_path, filename)

    def put(self, filename: str, stream: Stream, *, min_length: int=None, max_length: int=None):
        physical_path = self._get_physical_path(filename)
        physical_directory = dirname(physical_path)

        if not exists(physical_directory):
            makedirs(physical_directory, exist_ok=True)

        with open_stream(physical_path, mode='wb') as target_file:
            return copy_stream(stream, target_file, chunk_size=self.chunk_size, min_length=min_length, max_length=max_length)

    def delete(self, filename: str):
        remove(self._get_physical_path(filename))

    def open(self, filename: str, mode: str='rb') -> Stream:
        return open(self._get_physical_path(filename), mode=mode)

    def locate(self, attachment: 'Attachment') -> str:
        return '%s/%s' % (self.base_url, attachment.path)


class StoreManager(object):

    _stores = None
    _default = None
    _files_to_delete_after_commit = None
    _files_to_delete_after_rollback = None
    _files_orphaned = None

    def __init__(self, session, delete_orphan=False):
        self.session = session
        self.delete_orphan = delete_orphan
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
    def stores(self) -> dict:
        """
        The mapping `str -> store factory`.

        :type: dict[str] -> callable
        """
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
        """
        Calls the :meth:`.Store.cleanup` for each store is :attr:`.stores` and clears the :attr:`.stores` also.

        """
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

    # noinspection PyUnresolvedReferences
    def register_to_delete_after_commit(self, *files: Iterable['Attachment']):
        self._files_to_delete_after_commit.extend(files)

    def orphaned(self, *files: Iterable['Attachment']):
        if self.delete_orphan:
            self._files_orphaned.extend(files)

    def adopted(self, *files: Iterable['Attachment']):
        """
        Opposite of orphaned
        :param files:
        :return:
        """
        if not self.delete_orphan:
            return

        for f in files:
            if f in self._files_orphaned:
                self._files_orphaned.remove(f)

    # noinspection PyUnresolvedReferences
    def register_to_delete_after_rollback(self, *files: Iterable['Attachment']):
        self._files_to_delete_after_rollback.extend(files)

    def reset_files_state(self):
        self._files_to_delete_after_commit = []
        self._files_to_delete_after_rollback = []
        self._files_orphaned = []

    # noinspection PyUnusedLocal
    def on_commit(self, session):
        for f in self._files_to_delete_after_commit:
            f.delete()

        if self.delete_orphan:
            for f in self._files_orphaned:
                f.delete()

        self.reset_files_state()

    # noinspection PyUnusedLocal
    def on_rollback(self, session, transaction):
        for f in self._files_to_delete_after_rollback:
            f.delete()
        self.reset_files_state()

    # noinspection PyUnusedLocal
    def on_delete(self, session, instance):
        for attribute in _observing_attributes:
            if isinstance(instance, attribute.class_):
                self.register_to_delete_after_commit(getattr(instance, attribute.key).copy())

    @classmethod
    def observe_attribute(cls, attr, collection=False):

        if attr not in _observing_attributes:
            _observing_attributes.add(attr)

            # noinspection PyUnusedLocal
            def on_set_attr(target, value, old_value, initiator):
                if old_value is None or old_value in (symbol('NEVER_SET'), symbol('NO_VALUE')):
                    return

                store_manager = StoreManager.get_current_store_manager()
                if store_manager.delete_orphan:
                    if value is not old_value:
                        if collection:
                            if isinstance(old_value, dict):
                                store_manager.orphaned(*(set(old_value.values()) - set(value.values())))
                            else:
                                store_manager.orphaned(*(set(old_value) - set(value)))
                        else:
                            store_manager.orphaned(old_value)

            event.listen(attr, 'set', on_set_attr, propagate=True)
