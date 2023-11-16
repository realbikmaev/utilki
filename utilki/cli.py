from copy import deepcopy
from click import echo, prompt, Choice as choice, group, argument, option
import subprocess
from typing import Dict, Hashable, List, Tuple, TypeVar
from result import Result, Ok, Err


def sh(cmd: str, default=None) -> Result[List[str], str]:
    process = subprocess.run(
        [arg for arg in cmd.split(" ")],
        capture_output=True,
        text=True,
    )
    match process.returncode:
        case 0:
            return Ok([li.strip() for li in process.stdout.splitlines()])
        case _:
            echo(process.stderr)
            if default:
                return Ok(default)
            else:
                return Err(process.stderr)


def proc(cmd: str, timeout: float | None = None) -> Result[List[str], str]:
    process = subprocess.Popen(
        [arg for arg in cmd.split(" ")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.stdout is not None:
        for line in iter(process.stdout.readline, ""):
            echo(line.strip())
    return_code = process.wait(timeout=timeout)
    match return_code:
        case 0:
            return Ok([])
        case _:
            if process.stderr is not None:
                return Err("\n".join(process.stderr.readlines()))
    return Err("failed!")


K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


def append(map: Dict[K, List[V]], key: K, value: V) -> None:
    try:
        map[key]
    except KeyError:
        map[key] = []
    finally:
        map[key].append(value)


def sort_versions(versions: List[str]) -> List[str]:
    versions.sort(key=lambda x: tuple(map(int, x.split("."))), reverse=True)
    return versions


def list_versions() -> None:
    versions: List[str] = sh("pyenv install --list").unwrap_or([])
    global _all_versions
    for version in versions[1:]:
        if version.startswith("2.") or version.startswith("3."):
            if "dev" not in version and "rc" not in version:
                _all_versions.append(version)
    sort_versions(_all_versions)


def newest_version():
    versions = sh("pyenv versions").unwrap_or(["system"])
    numeric = [ve for ve in versions if "/" not in ve and len(ve) > 0]
    numeric.remove("system")
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
    newest_version()


def not_installed(version) -> Result[str, str]:
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
def venv(version):
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

    elif version not in _all_versions:
        print("lmao")
        echo(f"python version {version} is not installed")

    venv = prompt("enter venv name", type=str)
    create = sh(f"pyenv virtualenv {version} {venv}")

    match create:
        case Ok(_):
            echo(f"created venv {venv} with python version {version}")
        case Err(e):
            echo(e)
            echo("failed to create new venv! 😭")


if __name__ == "__main__":
    cli()
