import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pytest import fixture, raises

from utilki import TaskMixin
from utilki.task_mixin import get_date, parse_list, parse_options


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


def test_invalid_datetime(env_vars):
    with raises(ValueError, match="Invalid datetime format"):
        get_date("2022-02")


def test_parse_str_exception(env_vars):
    os.environ["lmao"] = "a: 1"
    task = Task.create()
    assert task.lmao == "a: 1"


def test_init_ellipsis(env_vars):
    mixin = TaskMixin.__init__()
    assert mixin is None


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
    with raises(TypeError):
        WrongDefaultTask.create()


@dataclass
class TypeWeDontSupport(TaskMixin):
    when_i_has_incorrect_default: frozenset = frozenset()


def test_task_create_invalid_type():
    with raises(TypeError):
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


@pydantic_dataclass
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


def test_invalid_list_format():
    with raises(ValueError, match="Invalid list format"):
        parse_list("1;2;3", int, "whatever")


def test_task_create_base_model_list(env_vars_list):
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
    del use_result


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


def test_optional_int_no_env_vars():
    os.unsetenv("how_many_times")
    task = OptionalIntTask.create()
    assert task == OptionalIntTask(how_many_times=None)


def test_parse_options():
    parse_options("1", int)


class WhatIfUserIsStupid(BaseModel, TaskMixin):
    his_iq: int = None  # type: ignore
    iq_of_his_parents: List[int] = None  # type: ignore


def test_what_if_user_is_stupid():
    with raises(TypeError):
        WhatIfUserIsStupid.create()


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


class JsonEncodedLists(BaseModel, TaskMixin):
    list_ints: List[int] = [1, 2, 3]
    list_strs: List[str] = ["1", "2", "3"]
    list_floats: List[float] = [1.0, 2.0, 3.0]
    list_bools: List[bool] = [True, False, True]
    ints: int = 1
    strs: str = "2"
    floats: float = 3.0
    bools: bool = True
    datetimes: datetime = datetime(2020, 1, 1)
    optional_int: Optional[int] = None
    optional_str: Optional[str] = None
    optional_float: Optional[float] = None
    optional_bool: Optional[bool] = None


@fixture
def json_encoded_lists_env_vars():
    os.environ["list_ints"] = json.dumps([4, 5, 6])
    os.environ["list_strs"] = json.dumps(["4", "5", "6"])
    os.environ["list_floats"] = json.dumps([4.0, 5.0, 6.0])
    os.environ["list_bools"] = json.dumps([False, True, False])
    os.environ["ints"] = json.dumps(4)
    os.environ["strs"] = json.dumps("4")
    os.environ["floats"] = json.dumps(4.0)
    os.environ["bools"] = json.dumps(False)
    os.environ["datetimes"] = json.dumps("2023-05-20")
    os.environ["optional_int"] = json.dumps(None)
    os.environ["optional_str"] = json.dumps(None)
    os.environ["optional_float"] = json.dumps(None)
    os.environ["optional_bool"] = json.dumps(None)
    yield
    del os.environ["list_ints"]
    del os.environ["list_strs"]
    del os.environ["list_floats"]
    del os.environ["list_bools"]
    del os.environ["ints"]
    del os.environ["strs"]
    del os.environ["floats"]
    del os.environ["bools"]
    del os.environ["datetimes"]
    del os.environ["optional_int"]
    del os.environ["optional_str"]
    del os.environ["optional_float"]
    del os.environ["optional_bool"]


def test_json_encoded_lists(json_encoded_lists_env_vars):
    task = JsonEncodedLists.create()
    assert task == JsonEncodedLists(
        list_ints=[4, 5, 6],
        list_strs=["4", "5", "6"],
        list_floats=[4.0, 5.0, 6.0],
        list_bools=[False, True, False],
        ints=4,
        strs="4",
        floats=4.0,
        bools=False,
        datetimes=datetime(2023, 5, 20),
        optional_int=None,
        optional_str=None,
        optional_float=None,
        optional_bool=None,
    )


class Wrong(TaskMixin):
    ayy: int = 1
    lmao: str = "2"
    when: datetime = datetime(2020, 1, 1)


def test_wrong_no_mixing_in():
    os.unsetenv("ayy")
    os.unsetenv("lmao")

    with raises(TypeError):
        Wrong.create()


def test_wrong_type_error_get_default():
    os.unsetenv("ayy")
    os.unsetenv("lmao")

    with raises(TypeError):
        Wrong.get_default("ayy")


def test_wrong_type_error_get_date():
    os.unsetenv("ayy")
    os.unsetenv("lmao")
    os.environ["when"] = "2022-30-20-20"

    with raises(TypeError):
        Wrong.get_default("ayy")


class DictInDict(BaseModel, TaskMixin):
    ayy: Dict[str, Dict[str, Any]] = {"lmao": {"when": "soon"}}


def test_dict_in_dict():
    task = DictInDict.create()
    assert task == DictInDict(ayy={"lmao": {"when": "soon"}})


def test_dict_in_dict_from_env():
    os.environ["ayy"] = json.dumps({"lmao": {"when": "not really soon"}})
    task = DictInDict.create()
    os.unsetenv("ayy")
    assert task == DictInDict(ayy={"lmao": {"when": "not really soon"}})


class FieldFactory(BaseModel, TaskMixin):
    date_from: str = Field(
        default_factory=lambda: str(datetime.now().date() - timedelta(days=1))
    )
    date_to: str = Field(default_factory=lambda: str(datetime.now().date()))


def test_base_model_field_factory():
    task = FieldFactory.create()
    assert task.date_from == str(datetime.now().date() - timedelta(days=1))
    assert task.date_to == str(datetime.now().date())


def test_base_model_field_factory_from_env():
    os.environ["date_from"] = "2020-01-01"
    os.environ["date_to"] = "2020-01-02"
    task = FieldFactory.create()
    assert task.date_from == "2020-01-01"
    assert task.date_to == "2020-01-02"


def test_update_method():
    del os.environ["ayy"]
    params = {"ayy": 420.0, "lmao": "lmao"}

    task = Task.create()
    task.update(params)
    task_default = Task(**params)
    assert task == task_default
