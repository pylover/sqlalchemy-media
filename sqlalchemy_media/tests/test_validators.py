
import unittest
import io
from os.path import dirname, abspath, join

from sqlalchemy_media.processors import MagicAnalyzer, WandAnalyzer, ContentTypeValidator, ImageValidator
from sqlalchemy_media.descriptors import AttachableDescriptor
from sqlalchemy_media.exceptions import ContentTypeValidationError, DimensionValidationError, AspectRatioValidationError


class ValidatorTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')
        cls.cat_jpeg = join(cls.stuff_path, 'cat.jpg')
        cls.cat_png = join(cls.stuff_path, 'cat.png')
        cls.dog_jpg = join(cls.stuff_path, 'dog_213X160.jpg')

    def test_content_type_validator(self):
        # guess content types from extension

        validator = ContentTypeValidator(['text/plain', 'image/jpeg'])
        analyzer = MagicAnalyzer()

        with AttachableDescriptor(io.BytesIO(b'Simple text')) as d:
            ctx = {}
            analyzer.process(d, ctx)
            validator.process(d, ctx)

        with AttachableDescriptor(self.cat_jpeg) as d:
            ctx = {}
            analyzer.process(d, ctx)
            validator.process(d, ctx)

        with AttachableDescriptor(self.cat_png) as d:
            ctx = {}
            analyzer.process(d, ctx)

            self.assertRaises(
                ContentTypeValidationError,
                validator.process, d, ctx
            )

            self.assertRaises(
                ContentTypeValidationError,
                validator.process, d, {}
            )

    def test_image_validator(self):
        # guess content types from extension

        analyzer = WandAnalyzer()

        with AttachableDescriptor(self.dog_jpg) as d:
            ctx = {}
            analyzer.process(d, ctx)
            ImageValidator((10, 10), (250, 250), content_types=['image/jpeg']).process(d, ctx)
            ImageValidator((10, 0), (0, 250)).process(d, ctx)
            ImageValidator((0, 0), (0, 250)).process(d, ctx)
            ImageValidator((0, 0), (0, 0)).process(d, ctx)

            # Lack of analyzer data
            self.assertRaises(
                DimensionValidationError,
                ImageValidator(maximum=(1, 0)).process, d, {}
            )

            # Maximum
            self.assertRaises(
                DimensionValidationError,
                ImageValidator(maximum=(212, 0)).process, d, ctx
            )

            self.assertRaises(
                DimensionValidationError,
                ImageValidator(maximum=(0, 159)).process, d, ctx
            )

            # Minimum
            self.assertRaises(
                DimensionValidationError,
                ImageValidator(minimum=(214, 0)).process, d, ctx
            )

            self.assertRaises(
                DimensionValidationError,
                ImageValidator(minimum=(0, 161)).process, d, ctx
            )

            self.assertRaises(
                AspectRatioValidationError,
                ImageValidator(min_aspect_ratio=1.4).process, d, ctx
            )

            self.assertRaises(
                AspectRatioValidationError,
                ImageValidator(max_aspect_ratio=1.3).process, d, ctx
            )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
