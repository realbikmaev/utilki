from collections.abc import Sized, Iterator
import logging
import subprocess
import sys
import traceback
from typing import Any, Callable, List, TypeVar, Generic, Iterable
from click import echo
import pandas as pd
from result import Err, Ok, Result


def sh(cmd: str, default: List[str] = []) -> Result[List[str], str]:
    process = subprocess.run(
        [arg for arg in cmd.split(" ")],
        capture_output=True,
        text=True,
    )
    match process.returncode:
        case 0:
            return Ok([li.strip() for li in process.stdout.splitlines()])
        case _:
            echo(process.stderr)
            if default:
                return Ok(default)
            else:
                return Err(process.stderr)


def proc(cmd: str, timeout: float | None = None) -> Result[List[str], str]:
    process = subprocess.Popen(
        [arg for arg in cmd.split(" ")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.stdout is not None:
        for line in iter(process.stdout.readline, ""):
            echo(line.strip())
    return_code = process.wait(timeout=timeout)
    match return_code:
        case 0:
            return Ok([])
        case _:
            if process.stderr is not None:
                return Err("\n".join(process.stderr.readlines()))
    return Err("failed!")


def set_global(name: str, value: Any):
    globals()[name] = value


def get_global(name: str, default: Any = None) -> Any:
    try:
        return globals()[name]
    except KeyError:
        return None if default is None else default


def incr(name: str) -> Any:
    value = get_global(name)
    if value is None:
        set_global(name, 0)
        return 0
    else:
        value += 1
        set_global(name, value)
        return value


class _logger:
    def __init__(self, name: str) -> None:
        set_global("_logger_name", name)
        self._hide_level_name = False

    def level(self, level: int):
        _get_logger().setLevel(level)
        return self

    def debug(self):
        return self.level(logging.DEBUG)

    def info(self):
        return self.level(logging.INFO)

    def warn(self):
        return self.level(logging.WARNING)

    def error(self):
        return self.level(logging.ERROR)

    def critical(self):
        return self.level(logging.CRITICAL)

    def use_print(self, use_print: bool):
        set_global("_use_print", use_print)
        return self

    def callback(self, callback: Callable[[str], None]):
        set_global("_callback", callback)
        return self

    def hide_level_name(self):
        self._hide_level_name = True

    def basic_config(self, level: int = logging.WARN):
        logging.basicConfig(
            format="%(asctime)s %(message)s"
            if self._hide_level_name
            else "%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            # NB: this is the default level of the root logger
            level=level,
            stream=sys.stdout,
        )
        return self

    def fn_level(self, level: int):
        """
        Set the level of the `log(message: str)` function.
        """
        set_global("_log_fn_level", level)
        return self

    def fn_debug(self):
        return self.fn_level(logging.DEBUG)

    def fn_info(self):
        return self.fn_level(logging.INFO)

    def fn_warn(self):
        return self.fn_level(logging.WARNING)

    def fn_error(self):
        return self.fn_level(logging.ERROR)

    def fn_critical(self):
        return self.fn_level(logging.CRITICAL)


def logger(name: str) -> _logger:
    return _logger(name)


def __log_fn(level: int) -> Callable[[str], None]:
    logger = _get_logger()
    if level == logging.DEBUG:
        return logger.debug
    elif level == logging.INFO:
        return logger.info
    elif level == logging.WARNING:
        return logger.warning
    elif level == logging.ERROR:
        return logger.error
    elif level == logging.CRITICAL:
        return logger.critical
    else:
        return logging.info


def _if_level(level: int, message: str):
    _use_print = get_global("_use_print", False)
    _callback = get_global("_callback", None)
    _logger = _get_logger()

    if _logger.level <= level:
        if _use_print:
            print(f"{message}", flush=True)
        if _callback:
            _callback(message)


def _get_logger() -> logging.Logger:
    logger_name = get_global("_logger_name")
    return logging.getLogger(logger_name)


def log(message: Any):
    message = str(message)
    level: int = get_global("_log_fn_level", logging.INFO)
    _if_level(level, message)
    __log_fn(level)(message)


def dbg(message: Any):
    message = str(message)
    logger = _get_logger()
    _if_level(logging.DEBUG, message)
    logger.debug(message)


def debug(message: Any):
    message = str(message)
    logger = _get_logger()
    _if_level(logging.DEBUG, message)
    logger.debug(message)


def info(message: Any):
    message = str(message)
    logger = _get_logger()
    _if_level(logging.INFO, message)
    logger.info(message)


def warn(message: Any):
    message = str(message)
    logger = _get_logger()
    _if_level(logging.WARNING, message)
    logger.warning(message)


def err(message: Any):
    message = str(message)
    logger = _get_logger()
    _if_level(logging.ERROR, message)
    logger.error(message)


def tb():
    if sys.exc_info()[0]:  # type: ignore # noqa
        message = traceback.format_exc()
        logger = _get_logger()
        _if_level(logging.ERROR, message)
        logger.error(message)


A = TypeVar("A")


class progress(Generic[A]):
    def __init__(
        self,
        iterator: Iterable[A],
        name: str = "",
        num_steps: int = 10,
        precision: int = 1,
        print_idx: bool = False,
    ) -> None:
        if not isinstance(iterator, Iterable):  # type: ignore
            raise ValueError("Passed object is not iterable")
        if not isinstance(iterator, Sized):
            raise ValueError("Passed object does not have a size")

        self.print_idx = print_idx
        self.iterator: Iterator[A] = iter(iterator)
        if isinstance(iterator, pd.DataFrame):
            self.iterator = iterator.iterrows()  # type: ignore
        self.len = len(iterator)
        self.name = name
        self.num_steps = num_steps
        if self.num_steps > self.len:
            self.num_steps = self.len

        if self.num_steps < 1:
            self.num_steps = 1

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
            log(msg)
        if self.index >= self.len:
            raise StopIteration
        else:
            self.index += 1
            return next(self.iterator)


if __name__ == "__main__":
    print(get_global("asdf"))
    set_global("asdf", 0)
    incr("asdf")
    print(get_global("asdf"))

    print(get_global("zcxv"))
    incr("zcxv")
    print(get_global("zcxv"))

    # def rev(msg):
    #     print(msg[::-1])
    #     pass

    # import time

    # logger("test").info().basic_config()

    # # too lazy rn to make a proper test suite
    # for i in progress(range(101), name="test1"):
    #     time.sleep(0.001)

    # for i in progress(
    #     range(7),
    #     name="test2",
    #     print_idx=True,
    #     num_steps=11,
    #     precision=3,
    # ):
    #     time.sleep(0.001)

    # for idx, i in enumerate(progress(["a", "b", "c"], name="test3")):
    #     time.sleep(0.001)

    # for i in progress([0.1, 0.2, 0.3], name="test4"):
    #     log(i)
    #     time.sleep(0.001)

    # log("hello world")

    # # logging.getLogger("ayy").setLevel(logging.INFO)
    # logger("ayy").info().fn_info().basic_config()

    # set_global("ayy", "lmao")
    # value = get_global("ayy")
    # log(value)

    # from datetime import datetime

    # err(datetime.now())

    # for i in progress([], name="test5"):
    #     time.sleep(0.001)

    # a = pd.DataFrame([{"a": 1, "b": 2}, {"a": 3, "b": 4}])

    # for idx, row in progress(a, name="test6"):  # type: ignore
    #     log(row)
    #     time.sleep(0.001)
