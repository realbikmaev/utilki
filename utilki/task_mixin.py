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


class TaskMixin:
    __dataclass_fields__: ClassVar[Dict[str, Any]]
    __fields__: ClassVar[Dict[str, Any]]

    @classmethod
    def create(cls):
        params: List[Tuple[str, Any]] = []
        if hasattr(cls, "__dataclass_fields__"):
            fields: Iterable[Field] = cls.__dataclass_fields__.values()
            for field in fields:
                params.append((field.name, field.type))
        if hasattr(cls, "__fields__"):
            model_fields: Iterable[ModelField] = cls.__fields__.values()
            for model_field in model_fields:
                params.append((model_field.name, model_field.outer_type_))
        task = cls(**{name: cls.parse(name, type) for name, type in params})
        return task

    @classmethod
    def get_default(cls, name_) -> Defaults:
        if default := os.getenv(name_):
            return default
        if hasattr(cls, "__dataclass_fields__"):
            field: Field = cls.__dataclass_fields__[name_]
            result: Any = field.default
            return result
        elif hasattr(cls, "__fields__"):
            model_field: ModelField = cls.__fields__[name_]
            return model_field.get_default()
        else:
            raise TypeError("Invalid type")

    @classmethod
    def get_date(cls, param):
        n = [int(n) for n in param.split("-")]
        if len(n) == 3:
            return datetime(n[0], n[1], n[2])
        elif len(n) == 6:
            return datetime(n[0], n[1], n[2], n[3], n[4], n[5])
        else:
            raise TypeError("Invalid datetime format")

    @classmethod
    def parse(cls, name_, type_):
        value = cls.get_default(name_)
        # print(f"parsing '{name_}' with type {type_} and value {value}")
        if isinstance(value, str):
            if type_ == List[int]:
                return tuple(map(int, value.split(",")))
            elif type_ == List[str]:
                return tuple(map(str, value.split(",")))
            elif type_ == List[float]:
                return tuple(map(float, value.split(",")))
            elif type_ == List[bool]:
                return tuple(map(parse_bool, value.split(",")))
            elif type_ == bool:
                return parse_bool(value)
            elif type_ == int:
                return int(value)
            elif type_ == float:
                return float(value)
            elif type_ == str:
                return str(value)
            elif type_ == datetime:
                has_t_or_colon = ":" in value or "T" in value
                num_parts = len(value.split("-"))
                if has_t_or_colon:
                    value = value.replace(" ", "-")
                    value = value.replace("T", "-")
                    value = value.replace(":", "-")
                    return cls.get_date(value)
                elif num_parts == 3:
                    return cls.get_date(value)
                else:
                    raise TypeError("Invalid datetime format")
        elif isinstance(value, list):
            if type_ in [List[int], List[str], List[float], List[bool]]:
                return value
        elif type_ == datetime:
            if isinstance(value, datetime):
                return value
            else:
                raise TypeError("Invalid default value")
        elif type_ in [bool, int, float]:
            return value
        else:
            raise TypeError("Invalid type")


def parse_bool(param):
    if param in ["True", "true", True]:
        return True
    elif param in ["False", "false", False]:
        return False
    else:
        raise TypeError("Invalid boolean format")
