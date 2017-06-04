"""

optionals Module
----------------

This module is a helper for handing optional packages.

Optional packages are not included in ``setup.py``. So :exc:`.OptionalPackageRequirementError` will be raised if
requested package is not provided.

"""

from sqlalchemy_media.exceptions import OptionalPackageRequirementError


# Libmagic

try:
    # noinspection PyPackageRequirements
    import magic
except ImportError:  # pragma: no cover
    magic = None


def magic_mime_from_buffer(buffer: bytes) -> str:
    """
    Try to detect mimetype using ``magic`` library.

    .. warning:: :exc:`.OptionalPackageRequirementError` will be raised if ``python-magic`` is not installed.

    :param buffer: buffer from header of file.

    :return: The mimetype
    """

    if magic is None:  # pragma: no cover
        raise OptionalPackageRequirementError('python-magic')

    return magic.from_buffer(buffer, mime=True)


# wand image

try:
    # noinspection PyPackageRequirements
    import wand
except ImportError:  # pragma: no cover
    wand = None


def ensure_wand():
    """

    .. warning:: :exc:`.OptionalPackageRequirementError` will be raised if ``wand`` is not installed.

    """

    if wand is None:  # pragma: no cover
        raise OptionalPackageRequirementError('wand')


# requests-aws4auth
try:
    # noinspection PyPackageRequirements
    from requests_aws4auth import AWS4Auth
except ImportError:  # pragma: no cover
    AWS4Auth = None


def ensure_aws4auth():
    """

    .. warning:: :exc:`.OptionalPackageRequirementError` will be raised if ``requests-aws4auth`` is not installed.

    """

    if AWS4Auth is None:  # pragma: no cover
        raise OptionalPackageRequirementError('requests-aws4auth')


# requests-aliyun
try:
    # noinspection PyPackageRequirements
    from aliyunauth import OssAuth as OS2Auth
except ImportError:  # pragma: no cover
    OS2Auth = None


def ensure_os2auth():
    """

    .. warning:: :exc:`.OptionalPackageRequirementError` will be raised if ``requests-aliyun`` is not installed.

    """

    if OS2Auth is None:  # pragma: no cover
        raise OptionalPackageRequirementError('requests-aliyun')


# paramiko
try:
    # noinspection PyPackageRequirements
    import paramiko
except ImportError:  # pragma: no cover
    paramiko = None


def ensure_paramiko():
    """

    .. warning:: :exc:`.OptionalPackageRequirementError` will be raised if ``paramiko`` is not installed.

    """

    if paramiko is None:  # pragma: no cover
        raise OptionalPackageRequirementError('paramiko')
