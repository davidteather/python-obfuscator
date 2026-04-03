import sys
from pathlib import Path
from typing import Annotated

import typer

import python_obfuscator
from python_obfuscator.techniques import one_liner as one_liner_technique
from python_obfuscator.version import __version__

DEFAULT_OUTPUT_DIR = "obfuscated"


def _resolved_output_path(input_path: Path) -> Path:
    """Write under ./obfuscated/, preserving path relative to cwd when possible."""
    cwd = Path.cwd().resolve()
    try:
        rel = input_path.resolve().relative_to(cwd)
    except ValueError:
        rel = Path(input_path.name)
    out = cwd / DEFAULT_OUTPUT_DIR / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def main(
    input_path: Annotated[
        Path,
        typer.Option(
            ...,
            "--input",
            "-i",
            help="File to obfuscate",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    stdout: Annotated[
        bool,
        typer.Option(
            "--stdout",
            help="Print obfuscated code to stdout instead of writing a file.",
        ),
    ] = False,
    include_one_liner: Annotated[
        bool,
        typer.Option(
            "--one-liner",
            "-ol",
            help="Include the one-liner obfuscation technique.",
        ),
    ] = False,
) -> None:
    resolved = input_path.expanduser().resolve()

    obfuscate = python_obfuscator.obfuscator()
    remove = []
    if not include_one_liner:
        remove.append(one_liner_technique)

    data = resolved.read_text()
    obfuscated_data = obfuscate.obfuscate(data, remove_techniques=remove)

    if stdout:
        typer.echo(obfuscated_data)
    else:
        out_path = _resolved_output_path(resolved)
        out_path.write_text(obfuscated_data)
        typer.secho(f"Wrote {out_path}", err=True)


def cli() -> None:
    if len(sys.argv) == 2 and sys.argv[1] in ("--version", "-V"):
        typer.echo(__version__)
        raise SystemExit(0)
    typer.run(main)
