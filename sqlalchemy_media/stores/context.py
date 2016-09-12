"""

For example, a function can take an image store to use as its parameter::

    def func(store):
        url = store.locate(image)
        # ...

    func(fs_store)

But, what if for various reasons it can't take an image store
as parameter?  You should vertically take it using scoped context::

    def func():
        current_store.locate(image)

    with store_context(fs_store):
        func()

What if you have to pass the another store to other subroutine?::

    def func(store):
        decorated_store = DecoratedStore(store)
        func2(decorated_store)

    def func2(store):
        url = store.locate(image)
        # ...

    func(fs_store)

The above code can be rewritten using scoped context::

    def func():
        decorated_store = DecoratedStore(current_store)
        with store_context(decorated_store):
            func2()

    def func2():
        url = current_store.locate(image)
        # ...

    with store_context(fs_store):
        func()

"""

import contextlib

try:
    import _thread
except ImportError:  
    import _dummy_thread as _thread  

from sqlalchemy_media.stores.base import Store
from sqlalchemy_media.stores.proxy import LocalProxyStore
from sqlalchemy_media.stores.exceptions import ContextError


def get_current_context_id() -> int:
    return _thread.get_ident()


#: (:class:`dict`) The dictionary of concurrent contexts to their stacks.
context_stacks = {}


def push_store_context(store: Store):
    """
    Manually pushes a store to the current stack.

    Although :func:`store_context()` and :keyword:`with` keyword are
    preferred than using it, it's useful when you have to push and pop
    the current stack on different hook functions like setup/teardown.

    :param store: the image store to set to the :data:`current_store`
    :type store: :class:`~sqlalchemy_media.store.Store`

    """
    context_stacks.setdefault(get_current_context_id(), []).append(store)


def pop_store_context() -> Store:
    """
    Manually pops the current store from the stack.

    Although :func:`store_context()` and :keyword:`with` keyword are
    preferred than using it, it's useful when you have to push and pop
    the current stack on different hook functions like setup/teardown.

    :returns: the current image store
    :rtype: :class:`~sqlalchemy_media.store.Store`

    """
    return context_stacks.setdefault(get_current_context_id(), []).pop()


@contextlib.contextmanager
def store_context(store: Store):
    """
    Sets the new (nested) context of the current image storage::

        with store_context(store):
            print current_store

    It could be set nestedly as well::

        with store_context(store1):
            print current_store  # store1
            with store_context(store2):
                print current_store  # store2
            print current_store  # store1 back

    :param store: the image store to set to the :data:`current_store`
    :type store: :class:`~sqlalchemy_media.stores.Store`

    """
    push_store_context(store)
    yield store
    store = pop_store_context()
    store.cleanup()


def get_current_store() -> Store:
    """
    The lower-level function of :data:`current_store`.  It returns
    the **actual** store instance while :data:`current_store` is a just
    proxy of it.

    :returns: the actual object of the currently set image store
    :rtype: :class:`~sqlalchemy_media.store.Store`

    """
    try:
        store = context_stacks.setdefault(get_current_context_id(), [])[-1]
    except IndexError:
        raise ContextError('not in store_context; use sqlalchemy_media.store_context()')
    return store


#: (:class:`LocalProxyStore`) The currently set context of the image store
#: backend.  It can be set using :func:`store_context()`.
current_store = LocalProxyStore(get_current_store)
