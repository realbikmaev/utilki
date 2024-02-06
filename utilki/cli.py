from copy import deepcopy
from click import echo, prompt, Choice as choice, group, argument
from typing import Dict, Hashable, List, TypeVar, Tuple
from result import Result, Ok, Err
from .log_utils import sh, proc


K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


def append(map: Dict[K, List[V]], key: K, value: V) -> None:
    try:
        map[key]
    except KeyError:
        map[key] = []
    finally:
        map[key].append(value)


def version_key(version: str) -> Tuple[int, ...]:
    return tuple(map(int, version.split(".")))


def sort_versions(versions: List[str]) -> List[str]:
    new_versions: List[str] = []

    for version in versions:
        try:
            version_key(version)
            new_versions.append(version)
        except ValueError:
            continue

    new_versions.sort(key=version_key, reverse=True)
    return new_versions


def list_versions() -> None:
    versions: List[str] = sh("pyenv install --list").unwrap_or([""])
    global _all_versions
    filtered: List[str] = []
    for version in versions[1:]:
        if version.startswith("2.") or version.startswith("3."):
            try:
                version_key(version)
                if "dev" not in version and "rc" not in version:
                    filtered.append(version)
            except ValueError:
                continue
    _all_versions = sort_versions(filtered)


def newest_version():
    versions = sh("pyenv versions --bare --skip-envs").unwrap_or(["system"])
    numeric = [ve for ve in versions if "/" not in ve and len(ve) > 0]
    try:
        numeric.remove("system")
    except Exception:
        pass
    sort_versions(numeric)
    global _installed
    global _all_versions
    _installed = deepcopy(numeric)
    return numeric[0]


_all_versions: List[str] = []
_installed: List[str] = []

if len(_all_versions) == 0:
    list_versions()

if len(_installed) == 0:
    newest = newest_version()


def not_installed(version: str) -> Result[str, str]:
    echo(f"python version {version} is not installed")
    response = prompt(
        f"python version {version} is not installed. install it?",
        type=choice(["y", "n"]),
        default="y",
    )
    if response == "y":
        install = proc(f"pyenv install {version}")
        match install:
            case Ok(_):
                echo(f"installed python version {version}")
                return Ok("accept_ok")
            case Err(e):
                echo(e)
                return Err("accept_err")
    elif response == "n":
        return Err("decline_err")
    return Err("unreachable")


@group(name="utilki")
def cli():
    pass


@cli.command()
@argument(
    "version",
    type=choice(_all_versions),
    default=_installed[0],
)
@argument(
    "venv",
    type=str,
    default="",
)
def create(version: str, venv: str = ""):
    """
    ut create [version] [venv]
    """
    global _all_versions
    global _installed

    if version == _installed[0]:
        echo(f"creating venv with default version {version}")
    else:
        echo(f"creating venv with python version {version}")
    if version not in _installed:
        install = not_installed(version)
        match install:
            case Ok(_):
                pass
            case Err("accept_err"):
                return
            case Err("decline_err"):
                return
            case _:
                pass

    elif version not in _all_versions:
        print("lmao")
        echo(f"python version {version} is not installed")

    venv = venv if venv else prompt("enter venv name", type=str)
    create = sh(f"pyenv virtualenv {version} {venv}")

    match create:
        case Ok(_):
            echo(f"created venv {venv} with python version {version}")
        case Err(e):
            echo(e)
            echo("failed to create new venv! 😭")


@cli.command()
@argument(
    "venv",
    type=str,
    default="",
)
def delete(venv: str = ""):
    """
    ut delete [venv]
    """
    venv = venv if venv else prompt("enter venv name", type=str)
    delete_ = proc(f"pyenv virtualenv-delete -f {venv}")

    match delete_:
        case Ok(_):
            echo(f"deleted venv {venv}")
        case Err(e):
            echo(e)
            echo("failed to delete venv! 😭")


@cli.command()
def v():
    """
    ut v
    """
    versions = sh("pyenv versions --bare --skip-aliases").unwrap_or([""])
    echo("\n".join(versions))


if __name__ == "__main__":
    cli()
