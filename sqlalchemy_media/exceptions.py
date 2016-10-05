
from os.path import join, dirname, abspath


class SqlAlchemyMediaException(Exception):
    """
    The base class for all exceptions
    """
    pass


class MaximumLengthIsReachedError(SqlAlchemyMediaException):
    """
    Indicates the maximum allowed file limit is reached.
    """

    def __init__(self, max_length: int):
        super().__init__('Cannot store files larger than: %d bytes' % max_length)


class MinimumLengthIsNotReachedError(SqlAlchemyMediaException):
    """
    Indicates the minimum allowed length is not \.
    """

    def __init__(self, min_length):
        super().__init__('Cannot store files smaller than: %d bytes' % min_length)


class ContextError(SqlAlchemyMediaException):
    """
    Exception related to :class:`.StoreManager`.
    """


class DefaultStoreError(SqlAlchemyMediaException):
    """
    Raised when no default store is registered.

    .. seealso:: :meth:`.StoreManager.register`.
    """

    def __init__(self):
        super(DefaultStoreError, self).__init__("Default store is not defined.")


class AnalyzeError(SqlAlchemyMediaException):
    """
    Raised when :class:`.Analyzer` can not analyze the stream.

    """


class ValidationError(SqlAlchemyMediaException):
    """
    Raised when :class:`.Validator` can not validate the stream.

    """


class ContentTypeValidationError(ValidationError):
    """
    Raised by :meth:`.Validator.validate` when the content type is missing or invalid.

    :param content_type: The invalid content type if any.
    """

    def __init__(self, content_type=None):

        if content_type is None:
            message = 'Content type is not provided.'
        else:
            message = 'Content type is not supported %s' % content_type

        super().__init__(message)


class DescriptorError(SqlAlchemyMediaException):
    """
    A sub-class instance of this exception may raised when an error has occurred in :class:`.BaseDescriptor` and
    it's subtypes.

    """


class DescriptorOperationError(DescriptorError):
    """
    Raised when a subclass of :class:`.BaseDescriptor` is abused.

    """


class OptionalPackageRequirementError(SqlAlchemyMediaException):
    """
    Raised when an optional package is missing.
    The constructor is trying to search for package name in requirements-optional.txt and find the requirement and
    it's version criteria to inform the user.

    :param package_name: The name of the missing package.
    """

    def __init__(self, package_name: str):

        # Searching for package name in requirements-optional.txt
        this_dir = dirname(__file__)
        filename = abspath(join(this_dir, '..', 'requirements-optional.txt'))
        with open(filename) as f:
            packages = [l for l in f if package_name in l]

        if not len(packages):
            raise ValueError('Cannot find the package: %s in file: %s' % (package_name, filename))

        super().__init__('The following packages are missing. in order please install them: %s' % ', '.join(packages))


class ThumbnailIsNotAvailableError(SqlAlchemyMediaException):
    """
    Raised when requested thumbnail is not available(generated) yet.

    """
