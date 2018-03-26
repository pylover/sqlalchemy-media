from .base import ImagingLibrary

from ..optionals import ensure_wand


class WandLibrary(ImagingLibrary):
    def __init__(self):
        ensure_wand()
        from wand.image import Image as WandImage
        from wand.exceptions import WandException
        self.WandImage = WandImage
        self.WandException = WandException

    def analyze(self, descriptor):
        try:
            # noinspection PyUnresolvedReferences
            with self.WandImage(file=descriptor)as img:
                return dict(
                    width=img.width,
                    height=img.height,
                    content_type=img.mimetype
                )
        except self.WandException as ex:
            raise AnalyzeError(str(ex))

