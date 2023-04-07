from datetime import datetime
import inspect
import os
import typing


class TaskMixin:
    @classmethod
    def create(cls):
        params = [
            (param.name, param.type)
            for param in cls.__dataclass_fields__.values()
        ]
        task = cls(**{name: cls.parse(name, type) for name, type in params})
        return task

    @classmethod
    def get_default(cls, param):
        return cls.__dataclass_fields__[param].default

    @classmethod
    def get_date(cls, param):
        num_parts = param.split("-")
        if len(num_parts) in [3, 6]:
            return datetime(*map(int, num_parts))
        else:
            raise TypeError("Invalid datetime format")

    @classmethod
    def parse(cls, param_name, param_type):
        param = os.getenv(param_name, cls.get_default(param_name))
        print(param, param_type, param_name)
        if inspect.isclass(param_type):
            print("isclass")
            if issubclass(param_type, datetime):
                if isinstance(param, datetime):
                    return param
                elif isinstance(param, str):
                    has_t_or_colon = ":" in param or "T" in param
                    num_parts = len(param.split("-"))
                    if has_t_or_colon:
                        param = param.replace(" ", "-")
                        param = param.replace("T", "-")
                        param = param.replace(":", "-")
                        return cls.get_date(param)
                    elif num_parts == 3:
                        return cls.get_date(param)
                    else:
                        raise TypeError("Invalid datetime format")
                else:
                    raise TypeError("Invalid default value")
            elif issubclass(param_type, bool):
                return parse_bool(param)
            elif issubclass(param_type, int):
                return int(param)
            elif issubclass(param_type, float):
                return float(param)
            elif issubclass(param_type, str):
                return str(param)
            else:
                raise TypeError("Invalid type")
        else:
            print("not isclass")
            if param_type == typing.Tuple[int]:
                return tuple(map(int, param.split(",")))
            elif param_type == typing.Tuple[str]:
                return tuple(map(str, param.split(",")))
            elif param_type == typing.Tuple[float]:
                return tuple(map(float, param.split(",")))
            elif param_type == typing.Tuple[bool]:
                return tuple(map(parse_bool, param.split(",")))


def parse_bool(param):
    if param in ["True", "true", True]:
        return True
    elif param in ["False", "false", False]:
        return False
    else:
        raise TypeError("Invalid boolean format")
