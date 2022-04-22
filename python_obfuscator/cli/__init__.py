import sys
import python_obfuscator
from python_obfuscator.techniques import one_liner
import argparse


def convert_file(args):
    file_path = args.input
    obfuscate = python_obfuscator.obfuscator()

    # removed techniques
    remove = []
    if not args.one_liner:
        remove.append(one_liner)

    with open(file_path, "r") as f:
        data = f.read()
        obfuscated_data = obfuscate.obfuscate(data, remove_techniques=remove)

    if args.replace:
        with open(file_path, "w+") as f:
            f.write(obfuscated_data)
    else:
        print(obfuscated_data)


def cli():
    parser = argparse.ArgumentParser(description="Process CLI args")
    parser.add_argument(
        "-i", "--input", help="File to obfuscate", required=True, type=str
    )
    parser.add_argument(
        "-r",
        "--replace",
        help="Replace the file specified",
        required=False,
        default=False,
        type=bool,
    )
    parser.add_argument(
        "-ol",
        "--one-liner",
        help="Add the one liner technique",
        required=False,
        default=False,
        type=bool,
    )
    args = parser.parse_args()

    convert_file(args)
