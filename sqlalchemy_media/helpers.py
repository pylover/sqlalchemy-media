
from typing import Any, Union, BinaryIO
import re


URI_REGEX_PATTERN = re.compile(
    "((?<=\()[A-Za-z][A-Za-z0-9+.\-]*://([A-Za-z0-9.\-_~:/?#\[\]@!$&'()*+,;=]|%[A-Fa-f0-9]{2})+(?=\)))|"
    "([A-Za-z][A-Za-z0-9+.\-]*://([A-Za-z0-9.\-_~:/?#\[\]@!$&'()*+,;=]|%[A-Fa-f0-9]{2})+)",
    re.IGNORECASE
)


def is_uri(x):
    return URI_REGEX_PATTERN.match(x) is not None


def open_stream(file_identifier: str) -> BinaryIO:
    raise NotImplementedError


def copy_stream(source: BinaryIO, target: BinaryIO, chunk_size: int) -> int:
    raise NotImplementedError
