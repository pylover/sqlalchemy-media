
import unittest
import io
from os.path import dirname, abspath, join

from sqlalchemy_media.analyzers import MagicAnalyzer, WandAnalyzer
from sqlalchemy_media.validators import ContentTypeValidator, ImageDimensionValidator
from sqlalchemy_media.descriptors import AttachableDescriptor
from sqlalchemy_media.exceptions import ContentTypeValidationError, DimensionValidationError


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

        self.assertIsNone(validator.validate(analyzer.analyze(AttachableDescriptor(io.BytesIO(b'Simple text')))))

        self.assertIsNone(validator.validate(analyzer.analyze(AttachableDescriptor(self.cat_jpeg))))

        self.assertRaises(
            ContentTypeValidationError,
            validator.validate,
            analyzer.analyze(AttachableDescriptor(self.cat_png))
        )

        self.assertRaises(
            ContentTypeValidationError,
            validator.validate,
            {}
        )

    def test_image_dimension_validator(self):
        # guess content types from extension

        analyzer = WandAnalyzer()

        def analyze(f):
            return analyzer.analyze(AttachableDescriptor(f))

        self.assertIsNone(ImageDimensionValidator((10, 10), (250, 250)).validate(analyze(self.dog_jpg)))
        self.assertIsNone(ImageDimensionValidator((10, 0), (0, 250)).validate(analyze(self.dog_jpg)))
        self.assertIsNone(ImageDimensionValidator((0, 0), (0, 250)).validate(analyze(self.dog_jpg)))
        self.assertIsNone(ImageDimensionValidator((0, 0), (0, 0)).validate(analyze(self.dog_jpg)))

        # Lack of analyzer data
        self.assertRaises(
            DimensionValidationError,
            ImageDimensionValidator(maximum=(639, 0)).validate,
            {}
        )

        # Maximum
        self.assertRaises(
            DimensionValidationError,
            ImageDimensionValidator(maximum=(639, 0)).validate,
            analyze(self.cat_jpeg)
        )

        self.assertRaises(
            DimensionValidationError,
            ImageDimensionValidator(maximum=(0, 479)).validate,
            analyze(self.cat_jpeg)
        )

        # Minimum
        self.assertRaises(
            DimensionValidationError,
            ImageDimensionValidator(minimum=(641, 0)).validate,
            analyze(self.cat_jpeg)
        )

        self.assertRaises(
            DimensionValidationError,
            ImageDimensionValidator(minimum=(0, 481)).validate,
            analyze(self.cat_jpeg)
        )

        #
        # self.assertRaises(
        #     DimensionValidationError,
        #     validator.validate,
        #     {}
        # )

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
