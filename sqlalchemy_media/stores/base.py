
from sqlalchemy_media.typing_ import FileLike


class Store:
    """
    The abstract base class for all stores.
    """

    # noinspection PyMethodMayBeStatic
    def cleanup(self):
        """
        In derived class should cleanup all dirty stuff created while storing and deleting file.
        If not overridden, no error will be raised.

        .. seealso:: :meth:`.StoreManager.cleanup`

        """
        pass

    def put(self, filename: str, stream: FileLike) -> int:
        """
        **[Abstract]**

        Should be overridden in inherited class and puts the file-like object as the given filename in the store.

        .. versionchanged:: 0.5

           - ``min_length`` has been removed.
           - ``max_length`` has been removed.

        :param filename: the target filename.
        :param stream: the source file-like object
        :return: length of the stored file.
        """
        raise NotImplementedError()  # pragma: no cover

    def delete(self, filename: str) -> None:
        """
        **[Abstract]**

        Should be overridden in inherited class and deletes the given file.

        :param filename: The filename to delete

        """
        raise NotImplementedError()  # pragma: no cover

    def open(self, filename: str, mode: str='rb') -> FileLike:
        """
        **[Abstract]**

        Should be overridden in inherited class and return a file-like object representing the file in the store.

        .. note:: Caller of this method is responsible to close the file-like object.

        :param filename: The filename to open.
        :param mode: same as the `mode` in famous :func:`.open` function.

        """
        raise NotImplementedError()  # pragma: no cover

    def locate(self, attachment) -> str:
        """
        **[Abstract]**

        If overridden in the inherited class, should locates the file's url to share in public space.

        :param attachment: The :class:`.Attachment` object to
        """
        raise NotImplementedError()  # pragma: no cover
