import io
from typing import Iterable

from PIL import Image as PilImage

from .descriptors import StreamDescriptor
from .exceptions import ContentTypeValidationError, DimensionValidationError, \
    AspectRatioValidationError, AnalyzeError
from .helpers import validate_width_height_ratio
from .mimetypes_ import guess_extension, guess_type, magic_mime_from_buffer
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
    Used to re-sampling, resizing, reformatting bitmaps.

    .. warning::

       - If ``width`` or ``height`` is given with ``crop``, Cropping will be
         processed after the resize.
       - If you pass both ``width`` and ``height``, aspect ratio may not be
         preserved.


    :param format: The image format. i.e jpeg, gif, png.
    :param width: The new image width.
    :param height: The new image height.
    :param crop: Used to crop the image.

    The crop argument is 4-tuple of (left, top, right, bottom)


        ImageProcessor(crop=(10, 10, 120, 230))

    """

    def __init__(self, fmt: str = None, width: int = None, height: int = None, crop=None):
        self.format = fmt.upper() if fmt else None
        self.width = width
        self.height = height
        self.crop = crop
        # self.crop = None if crop is None else {
        #   k: v if isinstance(v, str) else str(v) for k, v in crop.items()
        # }

    def _update_context(self, img: PilImage, format_, context: dict):
        mimetype = guess_type(f'a.{format_}'.lower())
        context.update(
            content_type=mimetype,
            width=img.width,
            height=img.height,
            extension=guess_extension(mimetype)
        )

    def process(self, descriptor: StreamDescriptor, context: dict):

        # Copy the original info
        # generating thumbnail and storing in buffer
        img = PilImage.open(descriptor)

        format_unchanged = self.format is None or img.format == self.format
        size_unchanged = (
            (self.width is None or img.width == self.width) and
            (self.height is None or img.height == self.height)
        )

        if self.crop is None and format_unchanged and size_unchanged:
            self._update_context(img, img.format, context)
            descriptor.prepare_to_read(backend='memory')
            return

        # Preserving format
        format_ = self.format or img.format

        if 'length' in context:
            del context['length']

        # opening the original file
        output_buffer = io.BytesIO()

        # Changing dimension if required.
        if not size_unchanged:
            width, height, _ = \
                validate_width_height_ratio(self.width, self.height, None)
            img = img.resize((
                width(img.size) if callable(width) else width,
                height(img.size) if callable(height) else height
            ))

        # Cropping
        if self.crop:
            img = img.crop(self.crop)

        img.save(output_buffer, format=format_)
        self._update_context(img, format_, context)
        output_buffer.seek(0)
        descriptor.replace(output_buffer, position=0, **context)


class ImageAnalyzer(Analyzer):
    """

    .. versionadded:: 0.16

    Analyze an image using available image library by calling the
    :classmethod:`.imaging.ImagingLibrary.get_available()

    .. note:: This object currently selects ``width``, ``height`` and
              ``mimetype`` of an image.

    """

    def process(self, descriptor: StreamDescriptor, context: dict):

        # This processor requires seekable stream.
        descriptor.prepare_to_read(backend='memory')

        try:
            img = PilImage.open(descriptor)
        except OSError:
            raise AnalyzeError('Cannot identify the requested image file')

        context.update(
            width=img.width,
            height=img.height,
            content_type=img.get_format_mimetype()
        )

        # prepare for next processor, calling this method is not bad and just
        # uses the memory temporary.
        descriptor.prepare_to_read(backend='memory')

