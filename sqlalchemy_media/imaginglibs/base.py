from abc import ABCMeta, abstractmethod

from ..exceptions import OptionalPackageRequirementError


class ImagingLibrary(metaclass=ABCMeta):
    @abstractmethod
    def analyze(self, descriptor):
        pass

    @classmethod
    def get_available(self):
        from .wand import WandLibrary
        try:
            return WandLibrary()
        except OptionalPackageRequirementError:
            # Raising the exception again, because there is onyy one image library available, but
            # after implementing the #97 the exception should be passed silently.
            raise

