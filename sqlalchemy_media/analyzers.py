
from sqlalchemy_media.descriptors import BaseDescriptor
from sqlalchemy_media.optionals import magic_mime_from_buffer, ensure_wand


class Analyzer(object):
    """
    The abstract base class for all analyzers.

    """

    def analyze(self, descriptor: BaseDescriptor) -> dict:
        """
        Should be overridden in inherited class and analyzes the given :class:`.BaseDescriptor` instance.

        .. note:: An instance of :exc:`.AnalyzeError` or sub-types may raised

        :param descriptor: An instance of :class:`.BaseDescriptor` to access the file while analyzing.
        :return: The analyze result.
        """
        raise NotImplementedError  # pragma: no cover


class MagicAnalyzer(Analyzer):
    """
    Analyze the file using the libmagic and it's Python wrapper: ``python-magic``.

    .. warning:: You should install the ``python-magic`` in order, to use this class. otherwise, an
                 :exc:`.OptionalPackageRequirementError` will be raised.
    """

    def analyze(self, descriptor: BaseDescriptor) -> dict:
        return dict(
            content_type=magic_mime_from_buffer(descriptor.get_header_buffer())
        )


class WandAnalyzer(Analyzer):
    """

    .. versionadded:: 0.4.0

    Analyze an image using ``wand``.

    .. warning:: You should install the ``wand`` in order, to use this class. otherwise, an
                 :exc:`.OptionalPackageRequirementError` will be raised.

    Use it as follow

    ..  testcode::

        from sqlalchemy import TypeDecorator, Unicode, Column, Integer
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.dialects.postgresql import JSONB

        from sqlalchemy_media import Image, WandAnalyzer


        class ProfileImage(Image):
           __analyzer__ = WandAnalyzer()

        Base = declarative_base()

        class Member(Base):
            __tablename__ = 'person'

            id = Column(Integer, primary_key=True)
            avatar = Column(ProfileImage.as_mutable(JSONB))

    The use it inside :class:`.ContextManager` context:

    ::

        from sqlalchemy_media import ContextManager

        session = <....>

        with ContextManager(session):
            me = Member(avatar=ProfileImage.create_from('donkey.jpg'))
            print(me.avatar.width)
            print(me.avatar.height)
            print(me.avatar.content_type)

    .. note:: This object currently setects ``width``, ``height`` and ``mimetype`` of the image.

    """

    def analyze(self, descriptor: BaseDescriptor) -> dict:
        ensure_wand()
        # noinspection PyPackageRequirements
        from wand.image import Image as WandImage

        with WandImage(file=descriptor)as img:
            return dict(
                width=img.width,
                height=img.height,
                content_type=img.mimetype
            )
