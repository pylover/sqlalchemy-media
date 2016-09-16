
class AttachmentError(Exception):
    pass


class UnboundAttachmentError(AttachmentError):
    def __init__(self, model):
        super(UnboundAttachmentError, self).__init__('Object: %r is not bound to a session.' % model)
