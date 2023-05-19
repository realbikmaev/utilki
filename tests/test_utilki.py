from typing import List, Optional
from utilki import TaskMixin
from dataclasses import dataclass
from datetime import datetime
import os
from pytest import raises, fixture
from pydantic import BaseModel


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
    with raises(ValueError, match="invalid literal"):
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
    when_i_has_incorrect_default: datetime = 100500  # type: ignore


def test_task_create_invalid_default():
    with raises(TypeError, match="Invalid default value"):
        WrongDefaultTask.create()


@dataclass
class TypeWeDontSupport(TaskMixin):
    when_i_has_incorrect_default: frozenset = frozenset()


def test_task_create_invalid_type():
    with raises(TypeError, match="Invalid type"):
        TypeWeDontSupport.create()


@fixture
def env_vars_list():
    os.environ["list_of_ints"] = "4,5,6"
    os.environ["list_of_strs"] = "4,5,6"
    os.environ["list_of_floats"] = "4.0,5.0,6.0"
    os.environ["list_of_bools"] = "True,False,true"
    yield
    del os.environ["list_of_ints"]
    del os.environ["list_of_strs"]
    del os.environ["list_of_floats"]
    del os.environ["list_of_bools"]


@fixture
def env_vars_list_str():
    os.environ["list_of_ints"] = "[4,5,6]"
    os.environ["list_of_strs"] = "[4,5,6]"
    os.environ["list_of_floats"] = "[4.0,5.0,6.0]"
    os.environ["list_of_bools"] = "[True,False,true]"
    yield
    del os.environ["list_of_ints"]
    del os.environ["list_of_strs"]
    del os.environ["list_of_floats"]
    del os.environ["list_of_bools"]


from pydantic.dataclasses import dataclass  # noqa


@dataclass
class TaskPydanticDataclass(TaskMixin):
    should_i_smoke: bool = False


def test_task_create_dataclass():
    os.environ["should_i_smoke"] = "False"
    task = TaskPydanticDataclass.create()
    assert task == TaskPydanticDataclass()
    del os.environ["should_i_smoke"]


class TaskBaseModel(BaseModel, TaskMixin):
    should_i_smoke: bool = False


def test_task_create_base_model():
    os.environ["should_i_smoke"] = "False"
    task = TaskBaseModel.create()
    assert task == TaskBaseModel()
    del os.environ["should_i_smoke"]


class TaskBaseModelList(BaseModel, TaskMixin):
    list_of_ints: List[int] = [1, 2, 3]
    list_of_strs: List[str] = ["1", "2", "3"]
    list_of_floats: List[float] = [1.0, 2.0, 3.0]
    list_of_bools: List[bool] = [True, False, True]


def test_task_create_base_model_list_default():
    task = TaskBaseModelList.create()
    assert task == TaskBaseModelList()


def test_task_create_base_model_list(env_vars_list):
    task = TaskBaseModelList.create()
    assert task == TaskBaseModelList(
        list_of_ints=[4, 5, 6],
        list_of_strs=["4", "5", "6"],
        list_of_floats=[4.0, 5.0, 6.0],
        list_of_bools=[True, False, True],
    )


def test_task_create_base_model_list_str(env_vars_list_str):
    task = TaskBaseModelList.create()
    assert task == TaskBaseModelList(
        list_of_ints=[4, 5, 6],
        list_of_strs=["4", "5", "6"],
        list_of_floats=[4.0, 5.0, 6.0],
        list_of_bools=[True, False, True],
    )


def use_task(task: Task):
    assert task == Task()
    return task


def test_eq_type_checks():
    task = Task.create()
    use_result = use_task(task)
    print(use_result)


class OptionalIntTask(BaseModel, TaskMixin):
    how_many_times: Optional[int] = None


@fixture
def optional_int_env_vars():
    os.environ["how_many_times"] = "None"
    yield
    del os.environ["how_many_times"]


def test_optional_int(optional_int_env_vars):
    task = OptionalIntTask.create()
    assert task == OptionalIntTask(how_many_times=None)


class OptionalTask(BaseModel, TaskMixin):
    ints: Optional[int] = 1
    strs: Optional[str] = "2"
    floats: Optional[float] = 3.0
    bools: Optional[bool] = True


@fixture
def optional_env_vars():
    os.environ["ints"] = "None"
    os.environ["strs"] = "null"
    os.environ["floats"] = ""
    os.environ["bools"] = "NULL"
    yield
    del os.environ["ints"]
    del os.environ["strs"]
    del os.environ["floats"]
    del os.environ["bools"]


def test_optional(optional_env_vars):
    task = OptionalTask.create()
    assert task == OptionalTask(ints=None, strs=None, floats=None, bools=None)
