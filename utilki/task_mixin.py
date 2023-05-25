from abc import abstractmethod
import json
import os
from datetime import datetime
from dataclasses import Field
from pydantic.fields import ModelField
from typing import (
    Any,
    ClassVar,
    Dict,
    Iterable,
    List,
    Tuple,
    Type,
    Union,
)


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
lists = [List[int], List[float], List[str], List[bool]]
options = [
    Union[int, None],
    Union[float, None],
    Union[str, None],
    Union[bool, None],
]
types_we_support = singles + lists + options

IsDefault = bool


def dbg(msg):
    if False:
        print(msg)


class TaskMixin:
    __dataclass_fields__: ClassVar[Dict[str, Any]]
    __fields__: ClassVar[Dict[str, Any]]

    @classmethod
    def __init__(cls, **kwargs):
        ...

    @classmethod
    def create(cls):
        params: List[Tuple[str, Any]] = []
        if hasattr(cls, "__dataclass_fields__"):
            fields: Iterable[Field] = cls.__dataclass_fields__.values()
            for field in fields:
                params.append((field.name, field.type))
        elif hasattr(cls, "__fields__"):
            model_fields: Iterable[ModelField] = cls.__fields__.values()
            for model_field in model_fields:
                params.append((model_field.name, model_field.annotation))
        else:
            raise TypeError("Invalid type")
        task = cls(**{name: cls.parse(name, type) for name, type in params})
        return task

    @classmethod
    def get_default(cls, name_) -> Tuple[IsDefault, Defaults]:
        env_var = os.getenv(name_)
        if env_var is not None:
            dbg(f"{name_} from env: {env_var}")
            return False, env_var
        if hasattr(cls, "__dataclass_fields__"):
            field: Field = cls.__dataclass_fields__[name_]
            result: Any = field.default
            dbg(f"{name_} default: {result}")
            return True, result
        elif hasattr(cls, "__fields__"):
            model_field: ModelField = cls.__fields__[name_]
            default_model = model_field.get_default()
            dbg(f"{name_} default: {default_model}")
            return True, default_model
        else:
            raise TypeError("Invalid type")

    @classmethod
    def parse(cls, name_, type_):
        is_default, value = cls.get_default(name_)
        if is_default:
            if type_ not in types_we_support:
                raise TypeError("Invalid type")
            if type_ != type(value) and type_ in singles:
                raise TypeError("Invalid type")
            if type_ in lists and not isinstance(value, list):
                raise TypeError("Invalid type")
            return value
        dbg(f"parsing '{name_}' with type {type_} and value {value}")
        if isinstance(value, str):
            res = parse_variations(type_, value, name_)
            dbg(f"res: {res}, type: {type_}, actual type {type(res)}")
            return res
        elif isinstance(value, list):
            if type_ in [List[int], List[str], List[float], List[bool]]:
                return value
        elif isinstance(value, datetime):
            if type_ == datetime:
                return value
        elif type_ in [int, str, float, bool]:
            if isinstance(value, type_):
                return value
        else:
            dbg(f"{name_}: {type_}\n'value' {value}: {type(value)}")
            raise TypeError("Invalid type")


def parse_bool(param):
    if param in ["True", "true", True]:
        return True
    elif param in ["False", "false", False]:
        return False
    else:
        raise TypeError("Invalid boolean format")


def parse_options(value, type_):
    if value in ["None", "none", None, "null", "NULL", ""]:
        return None
    else:
        return type_(value)


def parse_list(list_str: str, type_) -> List[Any]:
    if list_str.startswith("[") and list_str.endswith("]"):
        return json.loads(list_str)
    # TODO: make this a separate tuple parsing function
    # elif list_str.startswith("(") and list_str.endswith(")"):
    #     list_str.replace("(", "[")
    #     list_str.replace(")", "]")
    #     return json.loads(list_str)
    elif "," in list_str:
        return list(map(type_, list_str.split(",")))
    else:
        raise ValueError("Invalid list format")


def get_date(param: str):
    n = [int(n) for n in param.split("-")]
    if len(n) == 3:
        return datetime(n[0], n[1], n[2])
    elif len(n) == 6:
        return datetime(n[0], n[1], n[2], n[3], n[4], n[5])
    else:
        raise ValueError("Invalid datetime format")


def parse_variations(type_, value, name_):
    dbg(f"{name_} parse_variations({type_}, {value})")
    if type_ == List[int]:
        return parse_list(value, int)
    elif type_ == List[str]:
        return parse_list(value, str)
    elif type_ == List[float]:
        return parse_list(value, float)
    elif type_ == List[bool]:
        return parse_list(value, parse_bool)
    elif type_ == Union[int, None]:
        return parse_options(value, int)
    elif type_ == Union[str, None]:
        return parse_options(value, str)
    elif type_ == Union[float, None]:
        return parse_options(value, float)
    elif type_ == Union[bool, None]:
        return parse_options(value, parse_bool)
    elif type_ == bool:
        return parse_bool(value)
    elif type_ == int:
        return int(value)
    elif type_ == float:
        return float(value)
    elif type_ == str:
        dbg(f"str: {value}")
        try:
            res = json.loads(value)
            if type(res) == int:
                dbg(f"json.loads({value})")
                return str(res)
            else:
                return res
        except Exception:
            dbg(f"exception: {value}")
            return str(value)
    elif type_ == datetime:
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
