import io

from typing import Iterable

from sqlalchemy_media.typing_ import Dimension
from sqlalchemy_media.mimetypes_ import guess_extension
from sqlalchemy_media.exceptions import ContentTypeValidationError, DimensionValidationError, \
    AspectRatioValidationError, AnalyzeError
from sqlalchemy_media.helpers import validate_width_height_ratio
from sqlalchemy_media.descriptors import StreamDescriptor
from sqlalchemy_media.optionals import magic_mime_from_buffer, ensure_wand


class Processor(object):
    """

    .. versionadded:: 0.5

    Abstract base class for all processors.

    Processors are used to modify/replace the attachment before storing.

    """

    def process(self, descriptor: StreamDescriptor, context: dict) -> None:
        """
        **[Abstract]**


        Should be overridden in inherited class and apply the process on the file-like object. the result may be
        inserted info ``context`` argument.

        :param descriptor: The :class:`.BaseDescriptor` instance, to read the blob info from.
        :param context: A dictionary to put and get the info about the attachment. which as ``content_type``, ``width``,
                       ``height``, ``length`` and etc ...

        """
        raise NotImplementedError()  # pragma: no cover


class Analyzer(Processor):
    """

    .. versionadded:: 0.2

    .. versionchanged:: 0.5

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

    .. versionadded:: 0.2

    .. versionchanged:: 0.5

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

    .. versionadded:: 0.4

    .. versionchanged:: 0.5

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

    .. note:: This object currently selects ``width``, ``height`` and ``mimetype`` of the image.

    """

    def process(self, descriptor: StreamDescriptor, context: dict):
        ensure_wand()
        # noinspection PyPackageRequirements
        from wand.image import Image as WandImage
        from wand.exceptions import WandException

        # This processor requires seekable stream.
        descriptor.prepare_to_read(backend='memory')

        try:
            # noinspection PyUnresolvedReferences
            with WandImage(file=descriptor)as img:
                context.update(
                    width=img.width,
                    height=img.height,
                    content_type=img.mimetype
                )

        except WandException:
            raise AnalyzeError(str(WandException))

        # prepare for next processor, calling this method is not bad.
        descriptor.prepare_to_read(backend='memory')


class Validator(Processor):
    """

    .. versionadded:: 0.2

    .. versionchanged:: 0.5

       - Inherited from :class:`.Processor`
       - The ``validate`` method renamed to ``process`` to override the parent method.

    The abstract base class for all validators.

    """

    def process(self, descriptor: StreamDescriptor, context: dict) -> None:
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

    .. versionadded:: 0.2

    Assert content types.

    :param content_types: An iterable whose items are allowed content types.

    .. note:: :exc:`.ContentTypeValidationError` may be raised during validation.

    """

    def __init__(self, content_types: Iterable[str] = None):
        self.content_types = set(content_types)

    def process(self, descriptor: StreamDescriptor, context: dict):
        if 'content_type' not in context:
            raise ContentTypeValidationError()

        if context['content_type'] not in self.content_types:
            raise ContentTypeValidationError(context['content_type'], self.content_types)


class ImageValidator(ContentTypeValidator):
    """

    .. versionadded:: 0.4

    .. versionchanged:: 0.5

       - Renamed from ``ImageDimensionValidator`` to ``ImageValidator``.

    Validates image size

    :param minimum: Minimum allowed dimension (w, h).
    :param maximum: Maximum allowed dimension (w, h).
    :param content_types: An iterable whose items are allowed content types.
    :param min_aspect_ratio: Minimum allowed image aspect ratio.
    :param max_aspect_ratio: Maximum allowed image aspect ratio.

    .. versionadded:: 0.6

       - ``min_aspect_ratio`` and ``max_aspect_ratio``


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

    def __init__(self, minimum: Dimension = None, maximum: Dimension = None, content_types=None,
                 min_aspect_ratio: float = None, max_aspect_ratio: float = None):
        self.min_width, self.min_height = minimum if minimum else (0, 0)
        self.max_width, self.max_height = maximum if maximum else (0, 0)
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
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

        aspect_ratio = width / height
        if (self.min_aspect_ratio and self.min_aspect_ratio > aspect_ratio) or \
                (self.max_aspect_ratio and self.max_aspect_ratio < aspect_ratio):
            raise AspectRatioValidationError('Invalid aspect ratio %s / %s = %s, accepted_range: %s - %s' % (
                width,
                height,
                aspect_ratio,
                self.min_aspect_ratio,
                self.max_aspect_ratio
            ))


class ImageProcessor(Processor):
    """

    .. versionadded:: 0.5

    Used to re-sampling, resizing, reformatting bitmaps.

    .. warning::

       - If ``width`` or ``height`` is given with ``crop``, Cropping will be processed after the resize.
       - If you pass both ``width`` and ``height``, aspect ratio may not be preserved.

    :param fmt: This argument will be directly passing to ``wand``. so, for list of available choices, see:
                `ImageMagic Documentation <http://www.imagemagick.org/script/formats.php>`_

    :param width: The new image width.
    :param height: The new image height.
    :param crop: Used to crop the image.

                 .. versionadded:: 0.6

                 The crop dimension as a dictionary containing the keys described
                 `here <http://docs.wand-py.org/en/0.4.1/wand/image.html#wand.image.BaseImage.crop>`_.



                 Including you can
                 use percent ``%`` sing to automatically calculate the values from original image dimension::

                     ImageProcessor(crop=dict(width='50%', height='50%', gravity='center'))
                     ImageProcessor(crop=dict(width='10%', height='10%', gravity='south_east'))

                 Or::

                     ImageProcessor(crop=dict(
                        top='10%',
                        bottom='10%',
                        left='10%',
                        right='10%',
                        width='80%',
                        height='80%'
                     ))

                 Included from wand documentation::

                     +--------------------------------------------------+
                     |              ^                         ^         |
                     |              |                         |         |
                     |             top                        |         |
                     |              |                         |         |
                     |              v                         |         |
                     | <-- left --> +-------------------+  bottom       |
                     |              |             ^     |     |         |
                     |              | <-- width --|---> |     |         |
                     |              |           height  |     |         |
                     |              |             |     |     |         |
                     |              |             v     |     |         |
                     |              +-------------------+     v         |
                     | <--------------- right ---------->               |
                     +--------------------------------------------------+

    .. seealso::

       - ``crop`` `method <http://docs.wand-py.org/en/0.4.1/wand/image.html#wand.image.BaseImage.crop>`_.
       - ``gravity`` `argument <http://docs.wand-py.org/en/0.4.1/wand/image.html#wand.image.GRAVITY_TYPES>`_.
       - `Wand <http://docs.wand-py.org/>`_

    """

    def __init__(self, fmt: str = None, width: int = None, height: int = None, crop=None):
        self.format = fmt.upper() if fmt else None
        self.width = width
        self.height = height
        self.crop = crop
        # self.crop = None if crop is None else {k: v if isinstance(v, str) else str(v) for k, v in crop.items()}

    def process(self, descriptor: StreamDescriptor, context: dict):

        # Ensuring the wand package is installed.
        ensure_wand()
        # noinspection PyPackageRequirements
        from wand.image import Image as WandImage

        # Copy the original info
        # generating thumbnail and storing in buffer
        # noinspection PyTypeChecker
        img = WandImage(file=descriptor)

        if self.crop is None and (self.format is None or img.format == self.format) and (
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

            # Changing dimension if required.
            if self.width or self.height:
                width, height, _ = validate_width_height_ratio(self.width, self.height, None)
                img.resize(
                    width(img.size) if callable(width) else width,
                    height(img.size) if callable(height) else height
                )

            # Cropping
            if self.crop:
                img.crop(**{
                    key: int(int(value[:-1]) / 100 * (img.width if key in ('width', 'left', 'right') else img.height))
                    if key in ('left', 'top', 'right', 'bottom', 'width', 'height')
                    and isinstance(value, str) and '%' in value else value
                    for key, value in self.crop.items()
                    })

            img.save(file=output_buffer)

            context.update(
                content_type=img.mimetype,
                width=img.width,
                height=img.height,
                extension=guess_extension(img.mimetype)
            )

        output_buffer.seek(0)
        descriptor.replace(output_buffer, position=0, **context)
