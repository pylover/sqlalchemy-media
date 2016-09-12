import json

from sqlalchemy.types import TypeDecorator, VARCHAR


# noinspection PyAbstractClass
class Attachment(TypeDecorator):
    impl = VARCHAR

    def __init__(self, backend_type=None, *args, **kw):
        super(Attachment, self).__init__(*args, **kw)
        if backend_type:
            self.impl = backend_type

    @property
    def python_type(self):
        return dict

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

    def copy(self, **kw):
        return self.__class__(backend_type=self.impl, **kw)
