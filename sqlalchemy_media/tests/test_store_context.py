import unittest
import time
import threading

from sqlalchemy_media.stores import Store, current_store


# noinspection PyAbstractClass
class DummyStore(Store):
    pass


class StoreContextTestCase(unittest.TestCase):

    def test_context_stack(self):
        with DummyStore() as store1:
            self.assertIs(store1, current_store.get_current_store())
            self.assertIs(store1, Store.get_current_store())

            with DummyStore() as store2:
                self.assertIs(store2, current_store.get_current_store())
                self.assertIs(store2, Store.get_current_store())
                self.assertIsNot(store2, store1)

            self.assertIs(store1, current_store.get_current_store())
            self.assertIs(store1, Store.get_current_store())

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
                with DummyStore() as store1:
                    self.test_case.assertIs(store1, Store.get_current_store())
                    self.stat.store1 = Store.get_current_store()

                    with DummyStore() as store2:
                        self.test_case.assertIs(store2, Store.get_current_store())
                        self.stat.store2 = Store.get_current_store()

                        self.stat.ready = True
                        while self.stat.wait:
                            time.sleep(.7)

        thread1_stat = ThreadStat()
        thread2_stat = ThreadStat()

        thread1 = WorkerThread(thread1_stat, self)
        thread2 = WorkerThread(thread2_stat, self)

        thread1.start()
        thread2.start()

        while not (thread1_stat.ready and thread2_stat.ready):
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


if __name__ == '__main__':
    unittest.main()

