from io import BytesIO
from typing import Union, IO, Iterable, Any, Callable


Stream = Union[IO[BytesIO], BytesIO]
Attachable = Union[str, dict, Stream, Iterable[Iterable[Any]]]

