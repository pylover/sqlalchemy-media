
from typing import BinaryIO
from urllib.request import urlopen
import re

from sqlalchemy_media.typing import Stream
from sqlalchemy_media.exceptions import MaximumLengthIsReachedError, MinimumLengthIsNotReachedError


URI_REGEX_PATTERN = re.compile(
    "((?<=\()[A-Za-z][A-Za-z0-9+.\-]*://([A-Za-z0-9.\-_~:/?#\[\]@!$&'()*+,;=]|%[A-Fa-f0-9]{2})+(?=\)))|"
    "([A-Za-z][A-Za-z0-9+.\-]*://([A-Za-z0-9.\-_~:/?#\[\]@!$&'()*+,;=]|%[A-Fa-f0-9]{2})+)",
    re.IGNORECASE
)


def is_uri(x):
    return URI_REGEX_PATTERN.match(x) is not None


def open_stream(file_identifier: str, mode: str='rb') -> BinaryIO:
    if is_uri(file_identifier):
        return urlopen(file_identifier)
    else:
        return open(file_identifier, mode=mode)


def copy_stream(source: Stream, target: Stream, *, chunk_size: int=16*1024, min_length: int=None,
                max_length: int=None) -> int:
    length = 0
    while 1:
        buf = source.read(chunk_size)
        if not buf:
            break
        length += len(buf)

        if max_length is not None and length > max_length:
            raise MaximumLengthIsReachedError(max_length)
        target.write(buf)

    if min_length is not None and length < min_length:
        raise MinimumLengthIsNotReachedError(min_length)

    return length
