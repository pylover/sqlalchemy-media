
from typing import Iterable

from sqlalchemy_media.typing_ import Dimension
from sqlalchemy_media.exceptions import ContentTypeValidationError, DimensionValidationError


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

    :param content_types: An iterable whose items are allowed content types.

    .. note:: :exc:`.ContentTypeValidationError` may be raised during validation.

    """

    def __init__(self, content_types: Iterable[str]):
        self.content_types = set(content_types)

    def validate(self, analyze_result: dict):
        if 'content_type' not in analyze_result:
            raise ContentTypeValidationError()

        if analyze_result['content_type'] not in self.content_types:
            raise ContentTypeValidationError(analyze_result['content_type'])


class ImageDimensionValidator(Validator):
    """

    .. versionadded:: 0.4.0


    Validates image size

    :param minimum: Minimum allowed dimension (w, h).
    :param maximum: Maximum allowed dimension (w, h).

    .. note:: :exc:`.DimensionValidationError` may be raised during validation.

    Use it as follow

    ..  testcode::

        from sqlalchemy_media import Image, WandAnalyzer, ImageDimensionValidator


        class ProfileImage(Image):
           __analyzer__ = WandAnalyzer()
           __validator__ = ImageDimensionValidator((64, 48), (128, 96))


    ::

    .. note:: This object currently setects ``width``, ``height`` and ``mimetype`` of the image.


    """

    def __init__(self, minimum: Dimension=None, maximum: Dimension=None):
        self.min_width, self.min_height = minimum if minimum else (0, 0)
        self.max_width, self.max_height = maximum if maximum else (0, 0)

    def validate(self, analyze_result: dict):
        width = analyze_result.get('width')
        height = analyze_result.get('height')

        if not (abs(width or 0) and abs(height or 0)):
            raise DimensionValidationError('width and height are not found in analyze_result.')

        if self.min_width and self.min_width > width:
            raise DimensionValidationError('Minimum allowed width is: %d, but the %d is given.' % (
                self.min_width,
                width
            ))

        if self.min_height and self.min_height > height:
            raise DimensionValidationError('Minimum allowed height is: %d, but the %d is given.' % (
                self.min_height,
                height
            ))

        if self.max_width and self.max_width < width:
            raise DimensionValidationError('Maximum allowed width is: %d, but the %d is given.' % (
                self.max_width,
                width
            ))

        if self.max_height and self.max_height < height:
            raise DimensionValidationError('Maximum allowed height is: %d, but the %d is given.' % (
                self.max_height,
                height
            ))
