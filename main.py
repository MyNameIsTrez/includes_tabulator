import argparse
import re
from pathlib import Path


def tabulate_includes(input_directory_path):
    table = []

    for input_entry_path in input_directory_path.rglob("*"):
        extension = input_entry_path.suffix

        name = input_entry_path.name

        if extension in {".h", ".hh", ".hpp", ".h++", ".c", ".cc", ".cpp", ".c++"}:
            text = input_entry_path.read_text(encoding="latin1")

            matches = []
            for match_ in re.finditer(r"#\s*include\s*[\"\<](.*\/)?(.*)[\"\>]", text):
                matches.append(match_.group(2))

            if matches:
                table.append({"name": name, "includes": matches})

    return table


def add_parser_arguments(parser):
    parser.add_argument(
        "input_directory_path",
        type=Path,
        help="Path to the input directory containing the headers to tabulate",
    )
    parser.add_argument(
        "output_table_path",
        type=Path,
        help="Path to the output table that will be generated",
    )


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_parser_arguments(parser)
    args = parser.parse_args()

    table = tabulate_includes(args.input_directory_path)

    serialized = "\n".join(
        [line["name"] + ": " + " ".join(line["includes"]) for line in table]
    )
    args.output_table_path.write_text(serialized)


if __name__ == "__main__":
    main()
