
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import event

from sqlalchemy_media.helpers import is_uri


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

    def import_(self, x, **kwargs):
        if isinstance(x, str):
            if is_uri(x):
                return self.import_uri(x, **kwargs)
            else:
                return self.import_filename(x, **kwargs)
        else:
            return self.import_stream(x, **kwargs)

    def import_uri(self, uri, content_type=None):
        return NotImplemented

    def import_filename(self, filename, content_type=None):
        return NotImplemented

    def import_stream(self, stream, content_type=None):
        parent = self._parents
        attr_name = self


class NullAttachmentView(AttachmentView):
    pass
