
import io

from typing import Iterable

from sqlalchemy_media.typing_ import Dimension
from sqlalchemy_media.exceptions import ContentTypeValidationError, DimensionValidationError
from sqlalchemy_media.helpers import validate_width_height_ratio
from sqlalchemy_media.descriptors import StreamDescriptor
from sqlalchemy_media.optionals import magic_mime_from_buffer, ensure_wand


class Processor(object):
    """

    .. versionadded:: 0.5.0

    Abstract base class for all processors.

    Processors are used to modify/replace the attachment before storing.

    """

    def process(self, descriptor: StreamDescriptor, context: dict) -> None:
        """
        **[Abstract]**


        Should be overridden in inherited class and apply the process on the stream. the result may be inserted info
        ``context`` argument.

        :param descriptor: The :class:`.BaseDescriptor` instance, to read the blob info from.
        :param context: A dictionary to put and get the info about the attachment. which as ``content_type``, ``width``,
                       ``height``, ``length`` and etc ...

        """
        raise NotImplementedError()  # pragma: no cover


class Analyzer(Processor):
    """

    .. versionadded:: 0.2.0

    .. versionchanged:: 0.5.0

       - Inherited from :class:`.Processor`
       - The ``analyze`` method renamed to ``process`` to override the parent method.


    The abstract base class for all analyzers.

    """
    def process(self, descriptor: StreamDescriptor, context: dict):
        """
        Should be overridden in inherited class and analyzes the given :class:`.BaseDescriptor` instance.

        .. note:: An instance of :exc:`.AnalyzeError` or sub-types may raised



        """
        raise NotImplementedError  # pragma: no cover


class MagicAnalyzer(Analyzer):
    """

    .. versionadded:: 0.2.0

    .. versionchanged:: 0.5.0

       - Inherited from :class:`.Processor`
       - The ``analyze`` method renamed to ``process`` to override the parent method.

    Analyze the file using the libmagic and it's Python wrapper: ``python-magic``.

    .. warning:: You should install the ``python-magic`` in order, to use this class. otherwise, an
                 :exc:`.OptionalPackageRequirementError` will be raised.
    """

    def process(self, descriptor: StreamDescriptor, context: dict):
        context.update(
            content_type=magic_mime_from_buffer(descriptor.get_header_buffer())
        )


class WandAnalyzer(Analyzer):
    """

    .. versionadded:: 0.4.0

    .. versionchanged:: 0.5.0

       - Inherited from :class:`.Processor`
       - The ``analyze`` method renamed to ``process`` to override the parent method.

    Analyze an image using ``wand``.

    .. warning:: You should install the ``wand`` in order, to use this class. otherwise, an
                 :exc:`.OptionalPackageRequirementError` will be raised.

    Use it as follow

    ..  testcode::

        from sqlalchemy import TypeDecorator, Unicode, Column, Integer
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.dialects.postgresql import JSONB

        from sqlalchemy_media import Image, WandAnalyzer


        class ProfileImage(Image):
           __pre_processors__ = WandAnalyzer()

        Base = declarative_base()

        class Member(Base):
            __tablename__ = 'person'

            id = Column(Integer, primary_key=True)
            avatar = Column(ProfileImage.as_mutable(JSONB))

    The use it inside :class:`.ContextManager` context:

    ::

        from sqlalchemy_media import ContextManager

        session = <....>

        with ContextManager(session):
            me = Member(avatar=ProfileImage.create_from('donkey.jpg'))
            print(me.avatar.width)
            print(me.avatar.height)
            print(me.avatar.content_type)

    .. note:: This object currently setects ``width``, ``height`` and ``mimetype`` of the image.

    """

    def process(self, descriptor: StreamDescriptor, context: dict):
        ensure_wand()
        # noinspection PyPackageRequirements
        from wand.image import Image as WandImage

        descriptor.prepare_to_read(backend='memory')

        with WandImage(file=descriptor)as img:
            context.update(
                width=img.width,
                height=img.height,
                content_type=img.mimetype
            )


class Validator(Processor):
    """

    .. versionadded:: 0.2.0

    .. versionchanged:: 0.5.0

       - Inherited from :class:`.Processor`
       - The ``validate`` method renamed to ``process`` to override the parent method.

    The abstract base class for all validators.

    """

    def process(self,  descriptor: StreamDescriptor, context: dict) -> None:
        """
        **[Abstract]**

        Should be overridden in inherited class and validate the validate the ``context``.

        .. note:: It should be appended after the :class:`.Analyzer` to the :attr:`Attachment.__pre_processors__`.

        .. note:: An instance of :exc:`.ValidationError` or sub-types may raised

        :param descriptor: The :class:`.BaseDescriptor` instance, to read the blob info from.
        :param context: A dictionary to to validate.

        """
        raise NotImplementedError  # pragma: no cover


class ContentTypeValidator(Validator):
    """

    .. versionadded:: 0.2.0

    Assert content types.

    :param content_types: An iterable whose items are allowed content types.

    .. note:: :exc:`.ContentTypeValidationError` may be raised during validation.

    """

    def __init__(self, content_types: Iterable[str]=None):
        self.content_types = set(content_types)

    def process(self, descriptor: StreamDescriptor, context: dict):
        if 'content_type' not in context:
            raise ContentTypeValidationError()

        if context['content_type'] not in self.content_types:
            raise ContentTypeValidationError(context['content_type'], self.content_types)


class ImageValidator(ContentTypeValidator):
    """

    .. versionadded:: 0.4.0

    .. versionchanged:: 0.5.0

       - Renamed from ``ImageDimensionValidator`` to ``ImageValidator``.

    Validates image size

    :param minimum: Minimum allowed dimension (w, h).
    :param maximum: Maximum allowed dimension (w, h).
    :param content_types: An iterable whose items are allowed content types.

    .. note:: Pass ``0`` on ``None`` for disabling assertion for one of: ``(w, h)``.

    .. note:: :exc:`.DimensionValidationError` may be raised during validation.

    Use it as follow

    ..  testcode::

        from sqlalchemy_media import Image, WandAnalyzer, ImageValidator


        class ProfileImage(Image):
            __pre_processors__ = [
                WandAnalyzer(),
                ImageValidator((64, 48), (128, 96), content_types=['image/jpeg', 'image/png'])
            ]

    """

    def __init__(self, minimum: Dimension=None, maximum: Dimension=None, content_types=None):
        self.min_width, self.min_height = minimum if minimum else (0, 0)
        self.max_width, self.max_height = maximum if maximum else (0, 0)
        if content_types:
            super().__init__(content_types=content_types)

    def process(self, descriptor: StreamDescriptor, context: dict) -> None:
        if hasattr(self, 'content_types'):
            super().process(descriptor, context)

        width = context.get('width')
        height = context.get('height')

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


class ImageProcessor(Processor):
    """

    .. versionadded:: 0.5.0

    Used to re-sampling, resizing, reformatting bitmaps.

    :param fmt: This argument will be directly passing to ``wand``. so, for list of available choices, see:
                `ImageMagic Documentation <http://www.imagemagick.org/script/formats.php>`_

    :param width: The new image width.
    :param height: The new image height.


    .. warning:: If you pass both ``width`` and ``height``, aspect ratio may not be preserved.

    .. seealso:: `Wand <http://docs.wand-py.org/>`_

    """

    def __init__(self, fmt: str=None, width: int=None, height: int=None):
        self.format = fmt.upper() if fmt else None
        self.width = width
        self.height = height

    def process(self, descriptor: StreamDescriptor, context: dict, ):

        # Ensuring the wand package is installed.
        ensure_wand()
        # noinspection PyPackageRequirements
        from wand.image import Image as WandImage

        # Copy the original info
        # generating thumbnail and storing in buffer
        img = WandImage(file=descriptor)

        if (self.format is None or img.format == self.format) and (
                (self.width is None or img.width == self.width) and
                (self.height is None or img.height == self.height)):
            img.close()
            descriptor.prepare_to_read(backend='memory')
            return

        if 'length' in context:
            del context['length']

        # opening the original file
        output_buffer = io.BytesIO()
        with img:
            # Changing format if required.
            if self.format and img.format != self.format:
                img.format = self.format
                if 'extension' in context:
                    del context['extension']

            # Changing dimension if required.
            if self.width or self.height:
                width, height, _ = validate_width_height_ratio(self.width, self.height, None)
                img.resize(
                    width(img.size) if callable(width) else width,
                    height(img.size) if callable(height) else height
                )

            img.save(file=output_buffer)

            context.update(
                content_type=img.mimetype,
                width=img.width,
                height=img.height
            )

        output_buffer.seek(0)
        descriptor.replace(output_buffer, position=0, **context)
