import click
import subprocess


def get_list_of_python_versions():
    res = subprocess.run(
        ["pyenv", "install", "--list"],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        click.echo(res.stderr)
        return
    versions = res.stdout.splitlines()
    return [version.strip() for version in versions[1:]]


@click.group(name="utilki")
def cli():
    pass


@cli.command()
@click.argument(
    "python_version",
    type=click.Choice(get_list_of_python_versions()),
    default="3.8.10",
)
def venv(python_version):
    # Create the virtual environment with the given name and Python version
    venv_name = click.prompt("Enter venv name", type=str)
    res = subprocess.run(
        ["pyenv", "virtualenv", python_version, venv_name],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        if "is not installed" in res.stderr:
            response = click.prompt(
                f"Python version {python_version} is not installed. Install it?",
                type=click.Choice(["y", "n"]),
                default="y",
            )
            if response == "y":
                process = subprocess.Popen(
                    ["pyenv", "install", python_version],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for line in iter(process.stdout.readline, ""):  # type: ignore
                    click.echo(line.strip())
                return_code = process.wait()
                if return_code != 0:
                    click.echo("Installation failed")
                    return
                click.echo("Installation successful")

                res = subprocess.run(
                    ["pyenv", "virtualenv", python_version, venv_name],
                    capture_output=True,
                    text=True,
                )
                if res.returncode != 0:
                    click.echo(res.stderr)
                    return

    click.echo(
        f"Created venv `{venv_name}` with Python version {python_version}"
    )


if __name__ == "__main__":
    cli()
