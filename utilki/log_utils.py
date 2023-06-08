from collections.abc import Iterable, Sized, Iterator
import logging
from typing import Callable, Optional, TypeVar, Generic


_logger_name = ""
_use_print = False
_callback = None


def set_default_logger_name(name: str):
    global _logger_name
    _logger_name = name  # type: ignore


def set_use_print(use_print: bool):
    global _use_print
    _use_print = use_print  # type: ignore


def set_callback(callback: Callable):
    global _callback
    _callback = callback  # type: ignore


def dbg(message: str):
    global _logger_name
    global _callback
    global _use_print
    logger = logging.getLogger(_logger_name)  # type: ignore
    if logger.level <= logging.DEBUG:
        if _use_print:  # type: ignore
            print(f"{message}", flush=True)
        if _callback:  # type: ignore
            _callback(message)  # type: ignore
    logger.debug(message)


def log(message: str):
    global _logger_name
    global _callback
    global _use_print
    if _use_print:  # type: ignore
        print(f"{message}", flush=True)
    logging.getLogger(_logger_name).info(message)  # type: ignore
    if _callback:  # type: ignore
        _callback(message)  # type: ignore


A = TypeVar("A")


class progress(Generic[A]):
    def __init__(
        self,
        iterator: Iterable[A],
        name: str = "",
        num_steps: int = 10,
        precision: int = 1,
        print_idx: bool = False,
        logger_name: Optional[str] = None,
    ):
        if not isinstance(iterator, Iterable):
            raise ValueError("Passed object is not iterable")
        if not isinstance(iterator, Sized):
            raise ValueError("Passed object does not have a size")

        if logger_name is None:
            global _logger_name
            logger_name = _logger_name  # type: ignore

        self.logger = logging.getLogger(logger_name)

        self.print_idx = print_idx
        self.iterator: Iterator[A] = iter(iterator)
        self.len = len(iterator)
        self.name = name
        self.num_steps = num_steps
        if self.num_steps > self.len:
            msg = "num_steps > len(iterator), setting num_steps to len(iterator)"
            self.logger.error(msg)
            self.num_steps = self.len

        self.map = {}
        step_size = 100 / self.num_steps
        is_int = step_size.is_integer()
        for i in range(self.num_steps + 1):
            index = i * int(self.len / self.num_steps)
            percent = i * step_size
            percent_str = f"{percent:.{precision}f}%"
            if is_int:
                percent_str = f"{int(percent):d}%"
            self.map[index] = percent_str

        self.indices = set(self.map.keys())
        self.index = 0
        self.index_len = len(str(self.len))
        self.percent_len = max([len(p) for p in self.map.values()])

    def __iter__(self):
        return self

    def __next__(self) -> A:
        if self.index in self.indices:
            msg = f"{self.name} {self.map[self.index]:>{self.percent_len}}"
            if self.print_idx:
                msg += f" n={self.index:<{self.index_len}}"
            self.logger.info(msg)
        if self.index >= self.len:
            raise StopIteration
        else:
            self.index += 1
            return next(self.iterator)


if __name__ == "__main__":
    import time

    set_default_logger_name("progress")

    # setup basic logging format
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )

    # too lazy rn to make a proper test suite
    for i in progress(range(101), name="test1"):
        time.sleep(0.001)

    for i in progress(
        range(7),
        name="test2",
        print_idx=True,
        num_steps=11,
        precision=3,
        logger_name="lmao",
    ):
        time.sleep(0.001)

    for idx, i in enumerate(progress(["a", "b", "c"], name="test3")):
        time.sleep(0.001)

    for i in progress([0.1, 0.2, 0.3], name="test4"):
        print(i)
        time.sleep(0.001)

    def rev(msg):
        print(msg[::-1])
        pass

    set_use_print(True)
    set_default_logger_name("ayy")
    set_callback(rev)
    log("hello world")

    logging.getLogger("ayy").setLevel(logging.INFO)
    dbg("debug message")
