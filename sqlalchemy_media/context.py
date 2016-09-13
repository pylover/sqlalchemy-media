
try:
    import _thread
except ImportError:
    import _dummy_thread as _thread

try:
    import greenlet
except ImportError:
    greenlet = None

try:
    import stackless
except ImportError:
    stackless = None

if greenlet is not None:
    if stackless is None:
        get_id = greenlet.getcurrent
    else:

        def get_id():
            return greenlet.getcurrent(), stackless.getcurrent()

elif stackless is not None:
    get_id = stackless.getcurrent
else:
    get_id = _thread.get_ident

