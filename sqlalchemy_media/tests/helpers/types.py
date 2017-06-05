import json

from sqlalchemy import Unicode, TypeDecorator


# noinspection PyAbstractClass
class Json(TypeDecorator):  # pragma: no cover
    impl = Unicode

    def process_bind_param(self, value, engine):
        return json.dumps(value)

    def process_result_value(self, value, engine):
        if value is None:
            return None

        return json.loads(value)
