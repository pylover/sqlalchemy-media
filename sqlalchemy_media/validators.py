
from typing import Iterable

from sqlalchemy_media.exceptions import ContentTypeValidationError


class Validator(object):
    """
    The abstract base class for all validators.
    """

    def validate(self, analyze_result: dict) -> None:
        """
        **[Abstract]**

        Should be overridden in inherited class and validate the analyze info extracted by :meth:`.analyze`.

        .. note:: It should be called after the :meth:`.analyze` method has been called.

        .. note:: An instance of :exc:`.ValidationError` or sub-types may raised

        :param analyze_result: The analyzer result to validate.

        """
        raise NotImplementedError  # pragma: no cover


class ContentTypeValidator(Validator):
    """
    Assert content types.

    """

    def __init__(self, content_types: Iterable[str]):
        self.content_types = set(content_types)

    def validate(self, analyze_result: dict):
        if 'content_type' not in analyze_result:
            raise ContentTypeValidationError()

        if analyze_result['content_type'] not in self.content_types:
            raise ContentTypeValidationError(analyze_result['content_type'])
