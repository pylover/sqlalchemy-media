
from typing import Any, Union, BinaryIO
from urllib.request import urlopen
from select import select
import shutil
import re


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


def copy_stream(source: BinaryIO, target: BinaryIO, chunk_size: int=16*1024) -> int:
    length = 0
    while 1:
        buf = source.read(chunk_size)
        if not buf:
            break
        length += len(buf)
        target.write(buf)
    return length
