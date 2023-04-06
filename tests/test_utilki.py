from utilki import TaskMixin
from dataclasses import dataclass
from datetime import datetime
import os
from pytest import raises, fixture


@dataclass
class Task(TaskMixin):
    ayy: float = 69.69
    lmao: str = "420"
    when_to_smoke: datetime = datetime.today().replace(
        hour=4, minute=20, second=0, microsecond=0
    )
    should_i_smoke: bool = False
    how_many_times: int = 0


@fixture
def env_vars():
    os.environ["ayy"] = "996"
    os.environ["lmao"] = "42"
    os.environ["when_to_smoke"] = "2012-12-12 12:12:12"
    os.environ["should_i_smoke"] = "True"
    os.environ["how_many_times"] = "420"
    yield
    del os.environ["ayy"]
    del os.environ["lmao"]
    del os.environ["when_to_smoke"]
    del os.environ["should_i_smoke"]
    del os.environ["how_many_times"]


@fixture
def parsed_task() -> Task:
    return Task(
        ayy=996.0,
        lmao="42",
        when_to_smoke=datetime(
            year=2012,
            month=12,
            day=12,
            hour=12,
            minute=12,
            second=12,
        ),
        should_i_smoke=True,
        how_many_times=420,
    )


def test_task_create_default():
    task = Task.create()
    assert task == Task()


def test_task_create_env_vars(env_vars, parsed_task):
    task = Task.create()
    assert task == parsed_task


def test_task_create_invalid_datetime(env_vars):
    os.environ["when_to_smoke"] = "invalid datetime"
    with raises(TypeError, match="Invalid datetime format"):
        Task.create()


def test_task_create_invalid_datetime_2(env_vars):
    os.environ["when_to_smoke"] = "2012-12-12 12:12:12 invalid"
    with raises(TypeError, match="Invalid datetime format"):
        Task.create()


def test_valid_datetime(env_vars, parsed_task):
    os.environ["when_to_smoke"] = "2012-12-12T12:12:12"
    task = Task.create()
    assert task == parsed_task


def test_valid_datetime_2(env_vars, parsed_task):
    os.environ["when_to_smoke"] = "2012-12-12"
    task = Task.create()
    parsed_task.when_to_smoke = datetime(
        year=2012,
        month=12,
        day=12,
    )
    assert task == parsed_task


@fixture
def incorrect_env_vars():
    os.environ["ayy"] = "996"
    os.environ["lmao"] = "42"
    os.environ["when_to_smoke"] = "2012-12-12 12:12:12"
    os.environ["should_i_smoke"] = "tru"
    os.environ["how_many_times"] = "420"
    yield
    del os.environ["ayy"]
    del os.environ["lmao"]
    del os.environ["when_to_smoke"]
    del os.environ["should_i_smoke"]
    del os.environ["how_many_times"]


def test_task_create_invalid_bool(incorrect_env_vars):
    with raises(TypeError, match="Invalid boolean format"):
        Task.create()


@dataclass
class WrongDefaultTask(TaskMixin):
    when_i_has_incorrect_default: datetime = 100500


def test_task_create_invalid_default():
    with raises(TypeError, match="Invalid default value"):
        WrongDefaultTask.create()


@dataclass
class TypeWeDontSupport(TaskMixin):
    when_i_has_incorrect_default: frozenset = frozenset()


def test_task_create_invalid_type():
    with raises(TypeError, match="Invalid type"):
        TypeWeDontSupport.create()
