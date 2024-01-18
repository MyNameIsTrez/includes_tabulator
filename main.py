import argparse
import json
import re
from pathlib import Path

hpp_ext = {".h", ".hh", ".hpp", ".h++"}
cpp_ext = {".c", ".cc", ".cpp", ".c++"}

cpp_and_hpp_ext = hpp_ext | cpp_ext


def recursively_count_occurrences(table, occurrences, include, seen):
    if include in seen:
        return

    occurrences[include] = occurrences.get(include, 0) + 1

    if include in table:
        seen.add(include)

        for subinclude in table[include]:
            recursively_count_occurrences(table, occurrences, subinclude, seen)


def count_occurrences(table):
    occurrences = {}

    for name, includes in table.items():
        extension = Path(name).suffix
        if extension in cpp_ext:
            for include in includes:
                seen = set()
                recursively_count_occurrences(table, occurrences, str(include), seen)

    return occurrences


def tabulate_includes(input_directory_path):
    table = {}

    for input_entry_path in input_directory_path.rglob("*"):
        extension = input_entry_path.suffix

        name = input_entry_path.name

        if extension in cpp_and_hpp_ext:
            # print(input_entry_path)

            text = input_entry_path.read_text(encoding="latin1")

            matches = []
            for match_ in re.finditer(r"#\s*include\s*[\"\<](.*\/)?(.*)[\"\>]", text):
                matches.append(match_.group(2))

            if matches:
                assert not input_entry_path in table

                table[name] = matches

    return table


def add_parser_arguments(parser):
    parser.add_argument(
        "input_directory_path",
        type=Path,
        help="Path to the input directory containing the headers to tabulate",
    )
    parser.add_argument(
        "output_occurrences_path",
        type=Path,
        help="Path to the output occurrences JSON file that will be generated, that details how often each header is included",
    )


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_parser_arguments(parser)
    args = parser.parse_args()

    table = tabulate_includes(args.input_directory_path)

    occurrences = count_occurrences(table)
    occurrences["total_inclusions"] = sum(occurrences.values())
    occurrences = dict(
        sorted(occurrences.items(), key=lambda item: item[1], reverse=True)
    )
    with open(args.output_occurrences_path, "w") as f:
        json.dump(occurrences, f)


if __name__ == "__main__":
    main()
