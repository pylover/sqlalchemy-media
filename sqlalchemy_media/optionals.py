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
