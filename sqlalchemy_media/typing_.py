from io import BytesIO, FileIO
from typing import Union, IO, Iterable, Any, Tuple


FileLike = Union[IO[BytesIO], BytesIO, FileIO]
Attachable = Union[str, dict, FileLike, Iterable[Iterable[Any]]]
Dimension = Tuple[int, int]
