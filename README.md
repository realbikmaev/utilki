# utilki

utils that are frequently used by me and might be useful for others

## installation

```bash
pip install utilki
```

## TaskMixin

Mixin class that adds `create()` classmethod to dataclass you define as your task params. Useful when you have a lot of container based tasks executed on remote clusters (e.g. Kubernetes, Hashicorp Nomad, etc.). It reads task params from environment variables, parses, and validates them. 

Note: requires you 

```python
from utilki import TaskMixin

@dataclass
class Task(TaskMixin):
    ayy: float = 69.69
    lmao: str = "420"

os.environ["ayy"] = "42.42"
os.environ["lmao"] = "69"

t = Task.create()
print(f"ayy: {t.ayy}, type: {type(t.ayy)}")
# ayy: 42.42, type: <class 'float'>
print(f"lmao: {t.lmao}, type: {type(t.lmao)}")
# lmao: 69, type: <class 'str'>
```

## Cli

### Venv

```bash
utilki venv 3.8.10
```