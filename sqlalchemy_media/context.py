
try:
    import _thread
except ImportError:  # pragma: no cover
    import _dummy_thread as _thread

try:
    # noinspection PyPackageRequirements
    import greenlet
except ImportError:
    greenlet = None

try:
    import stackless
except ImportError:
    stackless = None

if greenlet is not None:  # pragma: no cover
    if stackless is None:
        get_id = greenlet.getcurrent
    else:

        def get_id():
            return greenlet.getcurrent(), stackless.getcurrent()

elif stackless is not None:  # pragma: no cover
    get_id = stackless.getcurrent
else:
    get_id = _thread.get_ident

