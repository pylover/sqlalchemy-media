
import io

from sqlalchemy_media.helpers import validate_width_height_ratio
from sqlalchemy_media.typing_ import Attachable, Dimension
from sqlalchemy_media.optionals import ensure_wand
from sqlalchemy_media.descriptors import BaseDescriptor


class Processor(object):
    """
    Abstract base class for all processors.

    Processors are used to modify/replace the attachment before storing.

    """

    def process(self, descriptor: BaseDescriptor, attachment_info: dict, ) -> (Attachable, dict):
        """
        **[Abstract]**


        Should be overridden in inherited class and apply the process on the stream.

        :return: The new stream and, it's info. and ``None, None`` to indicate that nothing has been modified.

        """
        raise NotImplementedError()  # pragma: no cover


class ImageProcessor(Processor):
    """
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

    def process(self, descriptor: BaseDescriptor, attachment_info: dict, ) -> (Attachable, dict):

        # Ensuring the wand package is installed.
        ensure_wand()
        # noinspection PyPackageRequirements
        from wand.image import Image as WandImage

        # Copy the original info
        info = attachment_info.copy()

        # generating thumbnail and storing in buffer
        img = WandImage(file=descriptor)

        if (self.format is None or img.format == self.format) and (
                (self.width is None or img.width == self.width) and
                (self.height is None or img.height == self.height)):
            return None, None

        if 'length' in info:
            del info['length']

        # opening the original file
        output_buffer = io.BytesIO()
        with img:
            # Changing format if required.
            if self.format and img.format != self.format:
                img.format = self.format
                if 'extension' in info:
                    del info['extension']

            # Changing dimension if required.
            if self.width or self.height:
                width, height, _ = validate_width_height_ratio(self.width, self.height, None)
                img.resize(
                    width(img.size) if callable(width) else width,
                    height(img.size) if callable(height) else height
                )

            img.save(file=output_buffer)

            info.update(
                content_type=img.mimetype,
                width=img.width,
                height=img.height
            )

        output_buffer.seek(0)
        return output_buffer, info
