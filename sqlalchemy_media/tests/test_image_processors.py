
import unittest
from os.path import dirname, abspath, join

from sqlalchemy_media.descriptors import AttachableDescriptor
from sqlalchemy_media.processors import ImageProcessor, ImageAnalyzer


class ImageProcessorTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')
        cls.cat_jpeg = join(cls.stuff_path, 'cat.jpg')
        cls.cat_png = join(cls.stuff_path, 'cat.png')
        cls.cat_png_alpha = join(cls.stuff_path, 'rgba-cat.png')
        cls.dog_jpg = join(cls.stuff_path, 'dog_213X160.jpg')

    def test_resize_reformat(self):
        # guess content types from extension

        with AttachableDescriptor(self.cat_png) as d:
            ctx = dict(
                length=100000,
                extension='.jpg',
            )
            ImageProcessor(fmt='jpeg', width=200).process(d, ctx)

            self.assertDictEqual(ctx, {
                'content_type': 'image/jpeg',
                'width': 200,
                'height': 150,
                'extension': '.jpg'
            })
        
        with AttachableDescriptor(self.cat_png_alpha) as d:
            ctx = dict(
                length=100000,
                extension='.jpg',
            )
            ImageProcessor(fmt='jpeg', width=200).process(d, ctx)

            self.assertDictEqual(ctx, {
                'content_type': 'image/jpeg',
                'width': 200,
                'height': 150,
                'extension': '.jpg'
            })

        with AttachableDescriptor(self.cat_jpeg) as d:
            # Checking when not modifying stream.
            ctx = dict()
            ImageProcessor().process(d, ctx)
            self.assertEqual(
                {
                    'content_type': 'image/jpeg',
                    'width': 640,
                    'height': 480,
                    'extension': '.jpg'
                }.items(),
                ctx.items()
            )

            # Checking when not modifying stream.
            ImageProcessor(fmt='jpeg').process(d, ctx)
            self.assertEqual(
                {
                    'content_type': 'image/jpeg',
                    'width': 640,
                    'height': 480,
                    'extension': '.jpg'
                }.items(),
                ctx.items()
            )

            ImageProcessor(fmt='jpeg', width=640).process(d, ctx)
            self.assertEqual(
                {
                    'content_type': 'image/jpeg',
                    'width': 640,
                    'height': 480,
                    'extension': '.jpg'
                }.items(),
                ctx.items()
            )


            ImageProcessor(fmt='jpeg', height=480).process(d, ctx)
            self.assertEqual(
                {
                    'content_type': 'image/jpeg',
                    'width': 640,
                    'height': 480,
                    'extension': '.jpg'
                }.items(),
                ctx.items()
            )

    def test_crop(self):
        with AttachableDescriptor(self.cat_jpeg) as d:
            # Checking when not modifying stream.
            ctx = dict()
            ImageProcessor(
                crop=(160, 120, 480, 360)
            ).process(d, ctx)
            ctx = dict()
            ImageAnalyzer().process(d, ctx)
            self.assertDictEqual(
                ctx,
                {
                    'content_type': 'image/jpeg',
                    'width': 320,
                    'height': 240,
                }
            )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
