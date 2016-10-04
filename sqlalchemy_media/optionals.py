
try:
    # noinspection PyPackageRequirements
    import magic
except ImportError:  # pragma: no cover
    magic = None


def magic_mime_from_buffer(buffer: bytes):
    if magic is None:  # pragma: no cover
        from sqlalchemy_media.exceptions import OptionalPackageRequirementError
        raise OptionalPackageRequirementError('python-magic')

    return magic.from_buffer(buffer, mime=True)
