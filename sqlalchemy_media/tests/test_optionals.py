
import unittest
from sqlalchemy_media.exceptions import OptionalPackageRequirementError


class OptionalPackagesTestCase(unittest.TestCase):

    def test_exception(self):
        ex = OptionalPackageRequirementError('python-magic')
        self.assertTrue(
            str(ex).startswith('The following packages are missing. in order please install them: python-magic >= ')
        )

        self.assertRaises(ValueError, OptionalPackageRequirementError, 'PackageThatNotFoundInRequirements-optional.txt')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
