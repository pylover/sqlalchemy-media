import io
from typing import Iterable

from .descriptors import StreamDescriptor
from .exceptions import ContentTypeValidationError, DimensionValidationError, \
    AspectRatioValidationError, AnalyzeError
from .helpers import validate_width_height_ratio, deprecated
from .imaginglibs import get_image_factory
from .mimetypes_ import guess_extension
from .optionals import magic_mime_from_buffer, ensure_wand
from .typing_ import Dimension


class Processor(object):
    """

    .. versionadded:: 0.5

    Abstract base class for all processors.

    Processors are used to modify/replace the attachment before storing.

    """

    def process(self, descriptor: StreamDescriptor, context: dict) -> None:
        """
        **[Abstract]**


        Should be overridden in inherited class and apply the process on the
        file-like object. The result may be inserted info ``context`` argument.

        :param descriptor: The :class:`.BaseDescriptor` instance, to read the
                           blob info from.
        :param context: A dictionary to put and get the info about the
                        attachment. Which as ``content_type``, ``width``,
                        ``height``, ``length`` and etc ...

        """
        raise NotImplementedError()  # pragma: no cover


class Analyzer(Processor):
    """

    .. versionadded:: 0.2

    .. versionchanged:: 0.5

       - Inherited from :class:`.Processor`
       - The ``analyze`` method renamed to ``process`` to override the parent
       method.


    The abstract base class for all analyzers.

    """

    def process(self, descriptor: StreamDescriptor, context: dict):
        """
        Should be overridden in inherited class and analyzes the given
        :class:`.BaseDescriptor` instance.

        .. note:: An instance of :exc:`.AnalyzeError` or sub-types may raised



        """
        raise NotImplementedError  # pragma: no cover


class MagicAnalyzer(Analyzer):
    """

    .. versionadded:: 0.2

    .. versionchanged:: 0.5

       - Inherited from :class:`.Processor`
       - The ``analyze`` method renamed to ``process`` to override the parent
         method.

    Analyze the file using the libmagic and it's Python wrapper:
    ``python-magic``.

    .. warning:: You should install the ``python-magic`` in order, to use this
                 class. otherwise, an :exc:`.OptionalPackageRequirementError`
                 will be raised.
    """

    def process(self, descriptor: StreamDescriptor, context: dict):
        context.update(
            content_type=magic_mime_from_buffer(descriptor.get_header_buffer())
        )


@deprecated
class WandAnalyzer(Analyzer):
    """
    .. deprecated:: 0.16

    .. versionadded:: 0.4

    .. versionchanged:: 0.5

       - Inherited from :class:`.Analyzer`
       - The ``analyze`` method renamed to ``process`` to override the parent
         method.

    Analyze an image using ``wand``.

    .. warning:: Installing ``wand`` is required for using this class.
                 otherwise, an :exc:`.OptionalPackageRequirementError` will be
                 raised.

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

    .. note:: This object currently selects ``width``, ``height`` and
              ``mimetype`` of the image.

    """

    def process(self, descriptor: StreamDescriptor, context: dict):
        ensure_wand()
        from wand.image import Image as WandImage
        from wand.exceptions import WandException

        # This processor requires seekable stream.
        descriptor.prepare_to_read(backend='memory')

        try:
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
       - The ``validate`` method renamed to ``process`` to override the parent
         method.

    The abstract base class for all validators.

    """

    def process(self, descriptor: StreamDescriptor, context: dict) -> None:
        """
        **[Abstract]**

        Should be overridden in inherited class and validate the validate the
        ``context``.

        .. note:: It should be appended after the :class:`.Analyzer` to
                  the :attr:`Attachment.__pre_processors__`.

        .. note:: An instance of :exc:`.ValidationError` or sub-types may
                  raised

        :param descriptor: The :class:`.BaseDescriptor` instance, to read the
                           blob info from.
        :param context: A dictionary to to validate.

        """
        raise NotImplementedError  # pragma: no cover


class ContentTypeValidator(Validator):
    """

    .. versionadded:: 0.2

    Assert content types.

    :param content_types: An iterable whose items are allowed content types.

    .. note:: :exc:`.ContentTypeValidationError` may be raised during
              validation.

    """

    def __init__(self, content_types: Iterable[str] = None):
        self.content_types = set(content_types)

    def process(self, descriptor: StreamDescriptor, context: dict):
        if 'content_type' not in context:
            raise ContentTypeValidationError()

        if context['content_type'] not in self.content_types:
            raise ContentTypeValidationError(
                context['content_type'], self.content_types
            )


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


    .. note:: Pass ``0`` on ``None`` for disabling assertion for one of:
              ``(w, h)``.

    .. note:: :exc:`.DimensionValidationError` may be raised during validation.

    Use it as follow

    ..  testcode::

        from sqlalchemy_media import Image, ImageAnalyzer, ImageValidator


        class ProfileImage(Image):
            __pre_processors__ = [
                ImageAnalyzer(),
                ImageValidator(
                    (64, 48),
                    (128, 96),
                    content_types=['image/jpeg', 'image/png']
                )
            ]

    """

    def __init__(self, minimum: Dimension = None, maximum: Dimension = None,
                 content_types=None, min_aspect_ratio: float = None,
                 max_aspect_ratio: float = None):
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
            raise DimensionValidationError(
                'width and height are not found in analyze_result.'
            )

        if self.min_width and self.min_width > width:
            raise DimensionValidationError(
                f'Minimum allowed width is: {self.min_width: d}, but the '
                f'{width: d} is given.'
            )

        if self.min_height and self.min_height > height:
            raise DimensionValidationError(
                f'Minimum allowed height is: {self.min_height: d}, but the '
                f'{height: d} is given.'
            )

        if self.max_width and self.max_width < width:
            raise DimensionValidationError(
                f'Maximum allowed width is: {self.max_width: d}, but the '
                f'{width: d} is given.'
            )

        if self.max_height and self.max_height < height:
            raise DimensionValidationError(
                f'Maximum allowed height is: {self.max_height: d}, but the '
                f'{height: d} is given.'
            )

        aspect_ratio = width / height
        if (self.min_aspect_ratio and self.min_aspect_ratio > aspect_ratio) \
                or (
                    self.max_aspect_ratio \
                    and self.max_aspect_ratio < aspect_ratio
                ):
            raise AspectRatioValidationError(
                f'Invalid aspect ratio {width} / {height} = {aspect_ratio},'
                f'accepted_range: '
                f'{self.min_aspect_ratio} - {self.max_aspect_ratio}'
            )


class ImageProcessor(Processor):
    """

    .. versionadded:: 0.5

    Used to re-sampling, resizing, reformatting bitmaps.

    .. warning::

       - If ``width`` or ``height`` is given with ``crop``, Cropping will be
         processed after the resize.
       - If you pass both ``width`` and ``height``, aspect ratio may not be
         preserved.

    :param fmt: This argument will be directly passing to ``Wand`` or
                ``Pillow``. so, for list of available choices, see:
                `ImageMagic Documentation
                <http://www.imagemagick.org/script/formats.php>`_

    :param width: The new image width.
    :param height: The new image height.
    :param crop: Used to crop the image.

    .. versionadded:: 0.6

    The crop dimension as a dictionary containing the keys described
    `here <http://docs.wand-py.org/en/0.4.1/wand/image.html#wand.image.BaseImage.crop>`_.

    Including you can
    use percent ``%`` sing to automatically calculate the values from original
    image dimension::

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

       - ``crop`` `method <http://docs.wand-py.org/en/0.4.1/wand/image.html#wand.image.BaseImage.crop>`_.  # noqa
       - ``gravity`` `argument <http://docs.wand-py.org/en/0.4.1/wand/image.html#wand.image.GRAVITY_TYPES>`_.
       - `Wand <http://docs.wand-py.org/>`_

    """

    def __init__(self, fmt: str = None, width: int = None, height: int = None, crop=None):
        self.format = fmt.upper() if fmt else None
        self.width = width
        self.height = height
        self.crop = crop
        # self.crop = None if crop is None else {
        #   k: v if isinstance(v, str) else str(v) for k, v in crop.items()
        # }

    def process(self, descriptor: StreamDescriptor, context: dict):

        from .imaginglibs import get_image_factory

        Image = get_image_factory()
        # Copy the original info
        # generating thumbnail and storing in buffer
        img = Image(file=descriptor)

        is_invalid_format = self.format is None or img.format == self.format
        is_invalid_size = (
            (self.width is None or img.width == self.width) and
            (self.height is None or img.height == self.height)
        )

        if self.crop is None and is_invalid_format and is_invalid_size:
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
                width, height, _ = \
                    validate_width_height_ratio(self.width, self.height, None)
                img.resize(
                    width(img.size) if callable(width) else width,
                    height(img.size) if callable(height) else height
                )

            # Cropping
            if self.crop:
                def get_key_for_crop_item(key, value):
                    crop_width_keys = ('width', 'left', 'right')
                    crop_keys = (
                        'left', 'top', 'right', 'bottom', 'width', 'height'
                    )

                    if key in crop_keys and isinstance(value, str) \
                            and '%' in value:
                        return int(int(value[:-1]) / 100 * (
                            img.width if key in crop_width_keys else img.height
                        ))

                    return value

                img.crop(**{
                    key: get_key_for_crop_item(key, value)
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


class ImageAnalyzer(Analyzer):
    """

    .. versionadded:: 0.16

    Analyze an image using available image library by calling the
    :classmethod:`.imaging.ImagingLibrary.get_available()

    .. warning:: If none of ``Wand`` or ``Pillow`` are installed the
                 :exc:`.OptionalPackageRequirementError` will be raised.

    .. note:: This object currently selects ``width``, ``height`` and
              ``mimetype`` of an image.

    """

    def process(self, descriptor: StreamDescriptor, context: dict):

        Image = get_image_factory()

        # This processor requires seekable stream.
        descriptor.prepare_to_read(backend='memory')

        with Image(file=descriptor)as img:
            context.update(
                width=img.width,
                height=img.height,
                content_type=img.mimetype
            )

        # prepare for next processor, calling this method is not bad and just
        # uses the memory temporary.
        descriptor.prepare_to_read(backend='memory')
