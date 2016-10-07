
import re
import warnings
import functools
from hashlib import md5

from sqlalchemy_media.typing_ import FileLike


URI_REGEX_PATTERN = re.compile(
    "((?<=\()[A-Za-z][A-Za-z0-9+.\-]*://([A-Za-z0-9.\-_~:/?#\[\]@!$&'()*+,;=]|%[A-Fa-f0-9]{2})+(?=\)))|"
    "([A-Za-z][A-Za-z0-9+.\-]*://([A-Za-z0-9.\-_~:/?#\[\]@!$&'()*+,;=]|%[A-Fa-f0-9]{2})+)",
    re.IGNORECASE
)


def is_uri(x):
    return URI_REGEX_PATTERN.match(x) is not None


def copy_stream(source, target: FileLike, *, chunk_size: int= 16 * 1024) -> int:
    length = 0
    while 1:
        buf = source.read(chunk_size)
        if not buf:
            break
        length += len(buf)
        target.write(buf)
    return length


def md5sum(f):
    if isinstance(f, str):
        file_obj = open(f, 'rb')
    else:
        file_obj = f

    try:
        checksum = md5()
        while True:
            d = file_obj.read(1024)
            if not d:
                break
            checksum.update(d)
        return checksum.digest()
    finally:
        if file_obj is not f:
            file_obj.close()


def validate_width_height_ratio(width: int = None, height: int = None, ratio: float = None):

    params = ratio, width, height
    param_count = sum(p is not None for p in params)
    if not param_count:
        raise ValueError('Pass one of: ratio, width, or height')
    elif param_count > 1:
        raise ValueError('Pass only one argument in ratio, width, or height; these parameters are exclusive from '
                         'each other')

    if width is not None:
        if not isinstance(width, int):
            raise TypeError('Argument width must be integer, not: %s' % type(width))
        elif width < 1:
            raise ValueError('Argument width must be a natural number, not: %s' % repr(width))

        def height(size):
            return int(size[1] * (width / size[0]))

    elif height is not None:
        if not isinstance(height, int):
            raise TypeError('Argument height must be integer, not %s' % type(height))
        elif height < 1:
            raise ValueError('Argument height must be natural number, not %s' % repr(height))

        def width(size):
            return int(size[0] * (height / size[1]))

    elif ratio is not None:
        if not isinstance(ratio, float):
            raise TypeError('Argument ratio must be float, not: %s' % type(ratio))

        if ratio > 1:
            raise ValueError('ratio must be less than `1.0` .')

        def width(size):
            return int(size[0] * ratio)

        def height(size):
            return int(size[1] * ratio)

    return width, height, ratio


def deprecated(func):  # pragma: no cover
    """
    This is a decorator which can be used to mark functions as deprecated. It will result in a warning being emitted
    when the function is used.

    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # Turn off filter
        warnings.warn("Call to deprecated function %s" % func.__name__, category=DeprecationWarning, stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # Reset filter
        return func(*args, **kwargs)

    return new_func
