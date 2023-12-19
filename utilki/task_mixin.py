import ast
import json
import os
from dataclasses import Field
from datetime import date, datetime
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterable,
    List,
    Tuple,
    TypeVar,
    Union,
)

from pydantic import Field as ModelField
from pydantic.fields import FieldInfo

Defaults = Union[
    datetime,
    bool,
    int,
    float,
    str,
    List[bool],
    List[int],
    List[float],
    List[str],
]


singles = [int, float, str, bool, datetime]
lists = [
    List[int],
    List[float],
    List[str],
    List[bool],
    List[datetime],
    List[List[int]],
    List[List[float]],
    List[List[str]],
    List[List[bool]],
]
options = [
    Union[int, None],
    Union[float, None],
    Union[str, None],
    Union[bool, None],
    Union[datetime, None],
    Union[List[int], None],
    Union[List[float], None],
    Union[List[str], None],
    Union[List[bool], None],
    Union[List[datetime], None],
]

dicts = (
    [Dict[str, Any], Dict[str, str], Dict[str, int], Dict[str, float]]
    + [
        Dict[str, Dict[str, Any]],
        Dict[str, Dict[str, str]],
        Dict[str, Dict[str, int]],
        Dict[str, Dict[str, float]],
    ]
    + [
        Dict[Any, Any],
        Dict[Any, str],
        Dict[Any, int],
        Dict[Any, float],
        Dict[Any, bool],
    ]
)

types_we_support = singles + lists + options + dicts


defaults = Union[
    int,
    float,
    str,
    bool,
    datetime,
    List[int],
    List[float],
    List[str],
    List[bool],
]

IsDefault = bool


class ParseError(Exception):
    pass


class TaskMixin:
    __dataclass_fields__: ClassVar[Dict[str, Field]]  # type: ignore
    # model_fields: ClassVar[Dict[str, FieldInfo]]

    @classmethod
    def __init__(cls, **kwargs: Any): ...

    @classmethod
    def create(cls):
        params: List[Tuple[str, Any]] = []  # type: ignore
        if hasattr(cls, "__dataclass_fields__"):
            fields: Iterable[Field[Any]] = cls.__dataclass_fields__.values()  # type: ignore # noqa
            for field in fields:
                params.append((field.name, field.type))
        elif hasattr(cls, "model_fields"):
            for field_name, model_field in cls.model_fields.items():  # type: ignore # noqa
                params.append((field_name, model_field.annotation))  # type: ignore # noqa
        else:
            raise TypeError("Invalid type")
        task = cls(**{name: cls.parse(name, type) for name, type in params})
        return task

    @classmethod
    def get_default(cls, name_: str) -> Tuple[IsDefault, Defaults]:
        env_var = os.environ.pop(name_, None)
        if env_var is not None:
            return False, env_var
        if hasattr(cls, "__dataclass_fields__"):
            result = cls.__dataclass_fields__[name_].default
            return True, result
        elif hasattr(cls, "model_fields"):
            model_field: FieldInfo = cls.model_fields[name_]  # type: ignore # noqa
            default_model = model_field.get_default(call_default_factory=True)  # type: ignore # noqa
            return True, default_model  # type: ignore
        else:
            raise TypeError("Invalid type")

    @classmethod
    def parse(cls, name_: str, type_: type):
        is_default, value = cls.get_default(name_)
        if is_default:
            if type_ not in types_we_support:
                raise TypeError("Invalid type")
            if type_ != type(value) and type_ in singles:
                raise TypeError("Invalid type")
            if type_ in lists and not isinstance(value, list):
                raise TypeError("Invalid type")
            if type_ in dicts and not isinstance(value, dict):
                raise TypeError("Invalid type")
            else:
                return value
        else:
            try:
                res = parse_variations(type_, value, name_)
            except Exception as e:
                raise ParseError(f"{name_=} {value=} {type_=})") from e
            return res

    def update(self, param_dict: Dict[str, Any]):
        for param, value in param_dict.items():
            if hasattr(self, param):
                setattr(self, param, value)
            else:
                raise ValueError(f"Invalid parameter {param}")


def parse_bool(param: str) -> bool:
    if param in {"True", "true", True}:
        return True
    elif param in {"False", "false", False}:
        return False
    else:
        msg = "Invalid boolean format"
        raise TypeError(msg)


T = TypeVar("T")


def parse_options(value: str, type_: Callable[[str], T]) -> Union[T, None]:
    if value in ["None", "none", None, "null", "NULL", ""]:
        return None
    else:
        return type_(value)


def parse_list(
    list_str: str,
    type_: Callable[[str], T],
    name_: str,
) -> List[T]:
    if list_str.startswith("[") and list_str.endswith("]"):
        try:
            return json.loads(list_str)
        except json.JSONDecodeError:
            return ast.literal_eval(list_str)
    elif "," in list_str:
        return list(map(type_, list_str.split(",")))
    else:
        raise ValueError(f"Invalid list format {name_}: {list_str}")


def get_date(param: str):
    n = [int(n) for n in param.split("-")]
    if len(n) == 3:
        return datetime(n[0], n[1], n[2])
    elif len(n) == 6:
        return datetime(n[0], n[1], n[2], n[3], n[4], n[5])
    else:
        raise ValueError("Invalid datetime format")


def parse_variations(type_: type, value: Any, name_: str):
    if type_ == bool:  # noqa: E721
        return parse_bool(value)
    elif type_ == int:  # noqa: E721
        return int(value)
    elif type_ == float:  # noqa: E721
        return float(value)
    elif type_ == List[int]:
        return parse_list(value, int, name_)
    elif type_ == List[str]:
        return parse_list(value, str, name_)
    elif type_ == List[float]:
        return parse_list(value, float, name_)
    elif type_ == List[bool]:
        return parse_list(value, parse_bool, name_)
    elif type_ == Union[int, None]:
        return parse_options(value, int)
    elif type_ == Union[str, None]:
        return parse_options(value, str)
    elif type_ == Union[float, None]:
        return parse_options(value, float)
    elif type_ == Union[bool, None]:
        return parse_options(value, parse_bool)
    elif type_ == Dict[int, Any]:
        return json.loads(value)
    elif type_ == Dict[str, Any]:
        return json.loads(value)
    elif type_ == Dict[float, Any]:
        return json.loads(value)
    elif type_ == Dict[bool, Any]:
        return json.loads(value)
    elif type_ == str:  # noqa: E721
        try:
            res = json.loads(value)
            if not isinstance(res, str):
                return str(res)
            else:
                return res
        except Exception:
            return str(value)
    elif type_ in [datetime, date]:
        # FIXME actually like use proper parsing lmao
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        has_t_or_colon = ":" in value or "T" in value
        num_parts = len(value.split("-"))
        if has_t_or_colon:
            value = value.replace(" ", "-")
            value = value.replace("T", "-")
            value = value.replace(":", "-")
            return get_date(value)
        elif num_parts == 3:
            return get_date(value)
        else:
            raise TypeError("Invalid datetime format")
    elif type_ in types_we_support:
        try:
            return json.loads(value)
        except Exception:
            try:
                return ast.literal_eval(value)
            except Exception:
                raise TypeError("Invalid type")
