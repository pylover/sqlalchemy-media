import unittest
import time
import threading

from sqlalchemy.orm.session import Session

from sqlalchemy_media.stores import StoreManager, Store
from sqlalchemy_media.exceptions import DefaultStoreError, ContextError


# noinspection PyAbstractClass
class DummyStore(Store):
    pass


class StoreContextTestCase(unittest.TestCase):

    def setUp(self):
        StoreManager.register('dummy', DummyStore, default=True)

    def test_default_store(self):

        with StoreManager(Session) as manager1:

            # Hacking StoreManager to raise error
            StoreManager._default = None
            self.assertRaises(DefaultStoreError, manager1.get)

            # making it default again
            StoreManager.make_default('dummy')
            self.assertIsNotNone(manager1.get())

        # unregister
        StoreManager.unregister('dummy')

    def test_unregister(self):
        # unregister
        self.assertRaises(KeyError, StoreManager.unregister, 'invalid_Id')

    def test_context_stack(self):

        self.assertRaises(ContextError, StoreManager.get_current_store_manager)

        with StoreManager(Session) as manager1:
            store1 = manager1.get()
            self.assertIs(store1, manager1.default_store)

            with StoreManager(Session) as manager2:
                store2 = manager2.get()
                self.assertIs(store2, manager2.default_store)
                self.assertIsNot(manager1, manager2)
                self.assertIsNot(store1, store2)

    def test_multithread(self):

        class ThreadStat(object):
            store1 = None
            store2 = None
            wait = True
            ready = False

        class WorkerThread(threading.Thread):

            def __init__(self, stat, test_case):
                self.stat = stat
                self.test_case = test_case
                super().__init__(daemon=True)

            def run(self):
                with StoreManager(Session) as manager1:
                    store1 = manager1.get()
                    self.test_case.assertIs(store1, manager1.default_store)
                    self.stat.store1 = store1

                    with StoreManager(Session) as manager2:
                        store2 = manager2.get()
                        self.test_case.assertIs(store2, manager2.default_store)
                        self.stat.store2 = store2
                        self.stat.ready = True

                        while self.stat.wait:
                            time.sleep(.7)

        thread1_stat = ThreadStat()
        thread2_stat = ThreadStat()

        thread1 = WorkerThread(thread1_stat, self)
        thread2 = WorkerThread(thread2_stat, self)

        thread1.start()
        thread2.start()

        while not (thread1_stat.ready and thread2_stat.ready):  # pragma: no cover
            time.sleep(.7)

        self.assertIsNot(thread1_stat.store1, thread1_stat.store2)
        self.assertIsNot(thread2_stat.store1, thread2_stat.store2)

        self.assertIsNot(thread1_stat.store1, thread2_stat.store1)
        self.assertIsNot(thread1_stat.store1, thread2_stat.store2)

        self.assertIsNot(thread1_stat.store2, thread2_stat.store1)
        self.assertIsNot(thread1_stat.store2, thread2_stat.store2)

        thread1_stat.wait = False
        thread2_stat.wait = False

        thread1.join()
        thread2.join()


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

