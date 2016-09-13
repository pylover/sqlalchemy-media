import contextlib

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


from sqlalchemy_media.stores.base import Store
from sqlalchemy_media.stores.proxy import LocalProxyStore
from sqlalchemy_media.stores.exceptions import ContextError

if greenlet is not None:
    if stackless is None:
        get_current_context_id = greenlet.getcurrent
    else:

        def get_current_context_id():
            return greenlet.getcurrent(), stackless.getcurrent()

elif stackless is not None:
    get_current_context_id = stackless.getcurrent
else:
    get_current_context_id = _thread.get_ident


context_stacks = {}


@contextlib.contextmanager
def store_context(store: Store):
    context_id = get_current_context_id()
    context_stacks.setdefault(context_id, []).append(store)
    yield store
    store = context_stacks.setdefault(context_id, []).pop()
    store.cleanup()


def get_current_store() -> Store:
    try:
        store = context_stacks.setdefault(get_current_context_id(), [])[-1]
    except IndexError:
        raise ContextError('not in store_context; use sqlalchemy_media.store_context()')
    return store


current_store = LocalProxyStore(get_current_store)
