"""

optionals Module
----------------

This module is a helper for handing optional packages.

Optional packages are not included in ``setup.py``.
So :exc:`.OptionalPackageRequirementError` will be raised if requested package
is not provided.

"""

from .exceptions import OptionalPackageRequirementError

# requests-aws4auth
try:
    from requests_aws4auth import AWS4Auth
except ImportError:  # pragma: no cover
    AWS4Auth = None


def ensure_aws4auth():
    """

    .. warning:: :exc:`.OptionalPackageRequirementError` will be raised if
                 ``requests-aws4auth`` is not installed.

    """

    if AWS4Auth is None:  # pragma: no cover
        raise OptionalPackageRequirementError('requests-aws4auth')


# requests-aliyun
try:
    from aliyunauth import OssAuth as OS2Auth
except ImportError:  # pragma: no cover
    OS2Auth = None


def ensure_os2auth():
    """

    .. warning:: :exc:`.OptionalPackageRequirementError` will be raised if
                 ``requests-aliyun`` is not installed.

    """

    if OS2Auth is None:  # pragma: no cover
        raise OptionalPackageRequirementError('requests-aliyun')


# paramiko
try:
    import paramiko
except ImportError:  # pragma: no cover
    paramiko = None


def ensure_paramiko():
    """

    .. warning:: :exc:`.OptionalPackageRequirementError` will be raised if
                 ``paramiko`` is not installed.

    """

    if paramiko is None:  # pragma: no cover
        raise OptionalPackageRequirementError('paramiko')


# google-cloud-storage
try:
    import google.cloud.storage
except ImportError:  # pragma: no cover
    google.cloud.storage = None


def ensure_gcs():
    """

    .. warning:: :exc:`.OptionalPackageRequirementError` will be raised if
                 ``google-cloud-storage`` is not installed.

    """

    if google.cloud.storage is None:  # pragma: no cover
        raise OptionalPackageRequirementError('google-cloud-storage')
