from io import BytesIO, FileIO, TextIOWrapper
from typing import Union, IO, Iterable, Any, Tuple


FileLike = Union[IO[BytesIO], BytesIO, FileIO, TextIOWrapper]
Attachable = Union[str, dict, FileLike, Iterable[Iterable[Any]]]
Dimension = Tuple[int, int]
