
from .exceptions import OptionalPackageRequirementError
from .optionals import ensure_wand


def get_image_factory():
    try:
        ensure_wand()
        from wand.image import Image as WandImage
        return WandImage
    except OptionalPackageRequirementError:
        # Raising the exception again, because currently there is only one image library
        # available, but after implementing the #97 the exception should be passed silently.
        raise

