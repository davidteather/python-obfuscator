from pathlib import Path
from typing import Annotated

import typer

import python_obfuscator
from python_obfuscator.techniques import one_liner as one_liner_technique


def main(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            help="File to obfuscate",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    replace: Annotated[
        bool,
        typer.Option(
            "--replace",
            "-r",
            help="Overwrite the input file with obfuscated code.",
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
    obfuscate = python_obfuscator.obfuscator()
    remove = []
    if not include_one_liner:
        remove.append(one_liner_technique)

    data = input_path.read_text()
    obfuscated_data = obfuscate.obfuscate(data, remove_techniques=remove)

    if replace:
        input_path.write_text(obfuscated_data)
    else:
        typer.echo(obfuscated_data)


def cli() -> None:
    typer.run(main)
