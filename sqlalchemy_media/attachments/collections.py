
from collections import Iterable
from sqlalchemy.ext.mutable import MutableList, MutableDict

from sqlalchemy_media.attachments.attachment import Attachment
from sqlalchemy_media.attachments.file import File
from sqlalchemy_media.stores import StoreManager


class AttachmentCollection(object):
    __item_type__ = Attachment

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        StoreManager.observe_attribute(attribute, collection=True)
        # noinspection PyUnresolvedReferences
        # noinspection PyProtectedMember
        super()._listen_on_attribute(attribute, coerce, parent_cls)


class AttachmentList(AttachmentCollection, MutableList):

    @classmethod
    def coerce(cls, index, value):

        if isinstance(value, Iterable):
            result = cls()
            for i in value:
                result.append(cls.__item_type__.coerce(index, i))
            return result

        return super().coerce(index, value)

    def append(self, x):
        super().append(x)
        StoreManager.get_current_store_manager().adopted(x)

    def remove(self, i):
        super().remove(i)
        StoreManager.get_current_store_manager().orphaned(i)

    def pop(self, *args):
        i = super().pop(*args)
        StoreManager.get_current_store_manager().orphaned(i)
        return i

    def extend(self, x):
        StoreManager.get_current_store_manager().adopted(*x)
        super().extend(x)

    def insert(self, i, x):
        StoreManager.get_current_store_manager().adopted(x)
        super().insert(i, x)

    def clear(self):
        StoreManager.get_current_store_manager().orphaned(*self)
        super().clear()

    def __delitem__(self, index):
        StoreManager.get_current_store_manager().orphaned(self[index])
        super().__delitem__(index)

    def __setitem__(self, index, value):
        old_value = self[index]
        store_manager = StoreManager.get_current_store_manager()
        if old_value:
            store_manager.orphaned(old_value)

        store_manager.adopted(value)
        super().__setitem__(index, value)

    def __setslice__(self, start, end, value):
        store_manager = StoreManager.get_current_store_manager()
        store_manager.orphaned(*[i for i in self[start:end] if i])
        store_manager.adopted(*value)
        super().__setslice__(start, end, value)

    def __delslice__(self, start, end):
        StoreManager.get_current_store_manager().orphaned(*[i for i in self[start:end] if i])
        super().__delslice__(start, end)


class AttachmentDict(AttachmentCollection, MutableDict):

    @classmethod
    def coerce(cls, index, value):

        if isinstance(value, dict) and not isinstance(value, (AttachmentDict, Attachment)):
            result = cls()
            for k, v in value.items():
                result[k] = cls.__item_type__.coerce(k, v)
            return result

        return super().coerce(index, value)

    def setdefault(self, key, value):
        StoreManager.get_current_store_manager().adopted(value)
        return super().setdefault(key, value)

    def update(self, *a, **kw):
        StoreManager.get_current_store_manager().adopted(kw.values())
        super().update(*a, **kw)

    def pop(self, *args):
        i = super().pop(*args)
        StoreManager.get_current_store_manager().orphaned(i)
        return i

    def popitem(self):
        k, v = super().popitem()
        StoreManager.get_current_store_manager().orphaned(v)
        return k, v

    def clear(self):
        StoreManager.get_current_store_manager().orphaned(*self.values())
        super().clear()

    def __delitem__(self, key):
        StoreManager.get_current_store_manager().orphaned(self[key])
        super().__delitem__(key)

    def __setitem__(self, key, value):
        StoreManager.get_current_store_manager().adopted(value)
        super().__setitem__(key, value)


class FileList(AttachmentList):
    __item_type__ = File


class FileDict(AttachmentDict):
    __item_type__ = File
