import threading
import unittest

from concurrent.futures import as_completed
from functools import partial
from typing import List

from .. import ThreadPoolExecutor


class TestFixture:
    def __init__(self) -> None:
        self.log: List[int] = []
        self.cond = threading.Condition()
        self.pending = 0

    def step(self) -> None:
        self.pending += 1
        with self.cond:
            self.cond.notify()

    def func(self, n: int) -> None:
        "Call in another thread.  Waits for .step()"
        self.log.append(n)
        with self.cond:
            while self.pending == 0:
                self.cond.wait()
            self.pending -= 1


class TpeTest(unittest.TestCase):
    def test_obeys_insertion_order(self) -> None:
        tf = TestFixture()
        with ThreadPoolExecutor(1) as t:
            f1 = t.submit(partial(tf.func, 1))
            f2 = t.submit(partial(tf.func, 2))
            f3 = t.submit(partial(tf.func, 3))
            tf.step()
            tf.step()
            tf.step()
            self.assertEqual(
                [f1, f2, f3],
                list(as_completed([f1, f2, f3])),
            )
            self.assertEqual([1, 2, 3], tf.log)

    def test_bump(self) -> None:
        tf = TestFixture()
        with ThreadPoolExecutor(max_workers=1) as t:
            f1 = t.submit(partial(tf.func, 1))
            f2 = t.submit(partial(tf.func, 2))
            f3 = t.submit(partial(tf.func, 3))
            assert f1.running()
            assert not f1.done()
            assert not f2.done()
            assert not f3.done()
            t.bump(f3)
            assert not f2.done()
            assert not f3.done()
            tf.step()
            tf.step()
            tf.step()

            f1.result()
            f2.result()
            f3.result()

            self.assertEqual([1, 3, 2], tf.log)
