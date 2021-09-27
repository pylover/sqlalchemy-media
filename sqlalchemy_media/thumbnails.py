import io
from PIL import Image as PilImage
from typing import Tuple, Type, Union

from .attachments import Thumbnail
from .descriptors import StreamDescriptor
from .helpers import validate_width_height_ratio
from .typing_ import FileLike


def generate_thumbnail(
    original_image: Union[FileLike, StreamDescriptor],
    width: int = None,
    height: int = None,
    ratio: float = None,
    ratio_precision: int = 5,
    thumbnail_type: Type[Thumbnail] = Thumbnail,
) -> Tuple[int, int, float, Thumbnail]:
    width, height, ratio = validate_width_height_ratio(
        width, height, ratio
    )
    thumbnail_buffer = io.BytesIO()
    format_ = 'jpeg'
    extension = '.jpg'

    # generating thumbnail and storing in buffer
    img = PilImage.open(original_image)

    # JPEG does not handle Alpha channel, switch to PNG
    if img.mode == 'RGBA':
        format_ = 'png'
        extension = '.png'

    with img:
        original_size = img.size

        if callable(width):
            width = width(original_size)
        if callable(height):
            height = height(original_size)

        width = int(width)
        height = int(height)

        thumbnail_image = img.resize((width, height))
        thumbnail_image.save(thumbnail_buffer, format_)

    thumbnail_buffer.seek(0)

    ratio = round(width / original_size[0], ratio_precision)
    thumbnail = thumbnail_type.create_from(
        thumbnail_buffer,
        content_type=f'image/{format_}',
        extension=extension,
        dimension=(width, height)
    )

    return width, height, ratio, thumbnail

