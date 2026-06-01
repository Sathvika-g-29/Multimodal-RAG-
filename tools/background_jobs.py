from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, TypeVar


T = TypeVar("T")

_EXECUTOR = ThreadPoolExecutor(max_workers=2)


def submit_background_job(fn: Callable[..., T], *args, **kwargs) -> Future[T]:
    return _EXECUTOR.submit(fn, *args, **kwargs)

