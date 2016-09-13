from sqlalchemy import event
from sqlalchemy.ext.mutable import MutableDict

from sqlalchemy_media.stores import Store, current_store


class AttachmentView(MutableDict):

    def __init__(self, instance_state, *args, **kwargs):

        self.instance_state = instance_state
        super().__init__(*args, **kwargs)

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        super()._listen_on_attribute(attribute, coerce, parent_cls)

        def init_scalar(target, value, dict_):
            if value is None:
                return NullAttachmentView(target)

            if isinstance(value, cls):
                return value
            else:
                return cls(target, value)

        event.listen(attribute, 'init_scalar', init_scalar, raw=True, propagate=True, retval=True)

    def import_(self, stream, content_type=None, store: Store=current_store):
        parent = self._parents
        attr_name = self


class NullAttachmentView(AttachmentView):
    pass
