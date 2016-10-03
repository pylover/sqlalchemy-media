from io import BytesIO, FileIO
from typing import Union, IO, Iterable, Any


Stream = Union[IO[BytesIO], BytesIO, FileIO]
Attachable = Union[str, dict, Stream, Iterable[Iterable[Any]]]

