
from sqlalchemy_media.descriptors import BaseDescriptor
from sqlalchemy_media.optionals import magic_mime_from_buffer


class Analyzer(object):
    """
    The abstract base class for all analyzers.

    """

    def analyze(self, descriptor: BaseDescriptor) -> dict:
        """
        Should be overridden in inherited class and analyzes the :class:`.BaseDescriptor` instance given in constructor.

        .. note:: An instance of :exc:`.AnalyzeError` or sub-types may raised

        :param descriptor: An instance of :class:`.BaseDescriptor` to access the file while analyzing.
        :return: The analyze result.
        """
        raise NotImplementedError  # pragma: no cover


class MagicAnalyzer(Analyzer):
    """
    Analyze the file using the libmagic and it's python-wrapper: python-magic.

    .. warning:: You should install the python-magic in order, to use this class. otherwise, an
                 :exc:`.OptionalPackageRequirementError` will be raised.
    """

    def analyze(self, descriptor: BaseDescriptor):
        return dict(
            content_type=magic_mime_from_buffer(descriptor.get_header_buffer())
        )
