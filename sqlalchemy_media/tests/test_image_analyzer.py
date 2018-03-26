import unittest
from os.path import dirname, abspath, join

from sqlalchemy_media.descriptors import AttachableDescriptor
from sqlalchemy_media.processors import ImageAnalyzer


class ImageAnalyzerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')
        cls.cat_jpeg = join(cls.stuff_path, 'cat.jpg')
        cls.cat_png = join(cls.stuff_path, 'cat.png')

    def test_image_analyzer(self):
        analyzer = ImageAnalyzer()
        with AttachableDescriptor(self.cat_jpeg) as d:
            ctx = {}
            analyzer.process(d, ctx)
            self.assertDictEqual(ctx, {
                'width': 640,
                'height': 480,
                'content_type': 'image/jpeg'
            })


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
