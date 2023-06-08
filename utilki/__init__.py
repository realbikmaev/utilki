# flake8: noqa

__version__ = "0.1.0"

from .task_mixin import TaskMixin
from .log_utils import (
    progress,
    set_logger_name,
    set_use_print,
    set_callback,
    log,
    dbg,
    info,
    err,
    warn,
    basic_config,
    set_global,
    get_global,
)
