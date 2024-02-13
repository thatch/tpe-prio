import concurrent.futures
import logging
import queue
from collections import deque
from concurrent.futures._base import Future
from typing import Any, Optional, Tuple

LOG = logging.getLogger(__name__)


class ThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    """
    Subclass of concurrent.futures.ThreadPoolExecutor that allows hinting that
    you're actively waiting on a result (to make sure it runs soon).
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        thread_name_prefix: str = "",
        initializer: Optional[Any] = None,
        initargs: Tuple[Any, ...] = (),
    ) -> None:
        super().__init__(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
            initializer=initializer,
            initargs=initargs,
        )
        self._work_queue = queue._PySimpleQueue()  # type: ignore

    def bump(self, f: Future[Any]) -> None:
        """
        If `f` is still in the work queue (not yet assigned to a thread), make
        it next to run.  Otherwise, do nothing (its result may already be
        ready).

        This method is O(n) but does contain some fast paths.  If the work item
        gets picked up after you call bump but before it is found, the whole
        queue is traversed.

        Workers can pick up work items during this time out of order (they just
        call .get, not protected by any lock), so expect some perturbation
        especially if your work items are especially quick to process.
        """
        if f.done() or f.running():
            LOG.debug("bump %s is a no-op", f)
            return
        with self._shutdown_lock:
            q: deque[Any] = self._work_queue._queue  # type: ignore[attr-defined]
            i = 0
            saved = None
            while i < len(q):
                q.rotate(-1)
                i += 1
                if q[0].future == f:
                    saved = q.popleft()
                    break
            else:
                # already put back where it started
                LOG.debug("bump %s slow-path", f)
                return

            LOG.debug("bump %s by %s steps", f, i)
            q.rotate(i)
            q.appendleft(saved)


__all__ = ["ThreadPoolExecutor"]
