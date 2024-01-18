import argparse
import re
from pathlib import Path

hpp_ext = {".h", ".hh", ".hpp", ".h++"}
cpp_ext = {".c", ".cc", ".cpp", ".c++"}

cpp_and_hpp_ext = hpp_ext | cpp_ext


def recursively_count_occurrences(table, occurrences, include):
    occurrences[include] = occurrences.get(include, 0) + 1

    if include in table:
        for subinclude in table[include]:
            recursively_count_occurrences(table, occurrences, subinclude)


def count_occurrences(table):
    occurrences = {}

    for name, includes in table.items():
        extension = Path(name).suffix
        if extension in cpp_ext:
            for include in includes:
                recursively_count_occurrences(table, occurrences, str(include))

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
        [str(name) + ": " + " ".join(includes) for name, includes in table.items()]
    )
    args.output_table_path.write_text(serialized)

    occurrences = count_occurrences(table)
    sorted_occurrences = dict(
        sorted(occurrences.items(), key=lambda item: item[1], reverse=True)
    )
    print("How often each header is included:")
    print(sorted_occurrences)


if __name__ == "__main__":
    main()
