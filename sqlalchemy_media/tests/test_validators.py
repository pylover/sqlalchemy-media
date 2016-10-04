
import unittest
import io
from os.path import dirname, abspath, join

from sqlalchemy_media.analyzers import MagicAnalyzer
from sqlalchemy_media.validators import ContentTypeValidator
from sqlalchemy_media.descriptors import AttachableDescriptor
from sqlalchemy_media.exceptions import ContentTypeValidationError


class ValidatorTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')
        cls.cat_jpeg = join(cls.stuff_path, 'cat.jpg')
        cls.cat_png = join(cls.stuff_path, 'cat.png')

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


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
