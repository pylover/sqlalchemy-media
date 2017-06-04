

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

    def __init__(self, min_length, length=None):
        super().__init__('Cannot store files smaller than: %d bytes, but the file length is: %s' % (min_length, length))


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
    Raised when :class:`.Analyzer` can not analyze the file-like object.

    """


class ValidationError(SqlAlchemyMediaException):
    """
    Raised when :class:`.Validator` can not validate the file-like object.

    """


class ContentTypeValidationError(ValidationError):
    """
    Raised by :meth:`.Validator.validate` when the content type is missing or invalid.

    :param content_type: The invalid content type if any.
    """

    def __init__(self, content_type=None, valid_content_types=None):

        if content_type is None:
            message = 'Content type is not provided.'
        else:
            message = 'Content type is not supported %s.' % content_type

        if valid_content_types:
            message += 'Valid options are: %s' % ', '.join(valid_content_types)

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

    __optional_packages__ = [
        'python-magic >= 0.4.12',
        'wand >= 0.4.3',
        'requests-aws4auth >= 0.9',
        'requests-aliyun >= 0.2.5'
    ]

    def __init__(self, package_name: str):

        # Searching for package name in requirements-optional.txt
        packages = [l for l in self.__optional_packages__ if package_name in l]

        if not len(packages):
            raise ValueError('Cannot find the package: %s.' % package_name)

        super().__init__('The following packages are missing. in order please install them: %s' % ', '.join(packages))


class ThumbnailIsNotAvailableError(SqlAlchemyMediaException):
    """
    Raised when requested thumbnail is not available(generated) yet.

    """


class DimensionValidationError(ValidationError):
    """
    Raises when ``width`` or ``height`` of the media is not meet the limitations.

    """


class AspectRatioValidationError(ValidationError):
    """
    Raises when the image aspect ratio is not valid.

    """


class S3Error(SqlAlchemyMediaException):
    """
    Raises when the image upload or delete to s3.

    """


class OS2Error(SqlAlchemyMediaException):
    """
    Raises when the image upload or delete to os2.

    """


class SSHError(SqlAlchemyMediaException):
    """
    Raises when the ssh command is failed.
    """
