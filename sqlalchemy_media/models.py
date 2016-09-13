from sqlalchemy import event
from sqlalchemy.ext.mutable import MutableDict, Mutable

from sqlalchemy_media.stores import Store, current_store


class Attachment(MutableDict):

    def __init__(self, instance_state, *args, **kwargs):

        self.instance_state = instance_state
        super().__init__(*args, **kwargs)

    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionary to instance of this class."""
        if not isinstance(value, cls):
            if isinstance(value, dict):
                return cls(value)
            return Mutable.coerce(key, value)
        else:
            return value

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        super()._listen_on_attribute(attribute, coerce, parent_cls)

        def init_scalar(target, value, dict_):
            if value is None:
                return NullAttachment(target)

            if isinstance(value, cls):
                return value
            else:
                return cls(target, value)

        event.listen(attribute, 'init_scalar', init_scalar, raw=True, propagate=True, retval=True)

    def attach(self, stream, content_type=None, store: Store=current_store):
        print(self.instance_state)


class NullAttachment(Attachment):
    pass
