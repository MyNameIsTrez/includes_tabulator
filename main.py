import argparse
import json
import re
from pathlib import Path

hpp_ext = {".h", ".hh", ".hpp", ".h++"}
cpp_ext = {".c", ".cc", ".cpp", ".c++"}

cpp_and_hpp_ext = hpp_ext | cpp_ext


def recursively_count_occurrences(table, meta, counts, include, seen):
    if include in seen:
        return

    counts[include] = counts.get(include, 0) + 1

    if include in table:
        seen.add(include)

        size = table[include]["size"]
        meta["total_included_bytes"] += size

        extension = Path(include).suffix
        if extension in hpp_ext:
            meta["total_included_hpp_bytes"] += size
        elif extension in cpp_ext:
            meta["total_included_cpp_bytes"] += size

        for subinclude in table[include]["includes"]:
            recursively_count_occurrences(table, meta, counts, subinclude, seen)


def count_occurrences(table):
    meta = {
        "total_included_bytes": 0,
        "total_included_hpp_bytes": 0,
        "total_included_cpp_bytes": 0,
    }
    counts = {}
    occurrences = {"meta": meta, "counts": counts}

    for name, value in table.items():
        includes = value["includes"]

        extension = Path(name).suffix
        if extension in cpp_ext:
            size = value["size"]
            meta["total_included_bytes"] += size
            meta["total_included_cpp_bytes"] += size

            for include in includes:
                seen = set()
                recursively_count_occurrences(table, meta, counts, str(include), seen)

    return occurrences


def get_header_table(input_directory_path):
    table = {}

    for input_entry_path in input_directory_path.rglob("*"):
        extension = input_entry_path.suffix

        name = input_entry_path.name

        if extension in cpp_and_hpp_ext:
            # print(input_entry_path)

            # The game's files are jank, so the default encoding crashes this program
            text = input_entry_path.read_text(encoding="latin1")

            includes = []
            for match_ in re.finditer(r"#\s*include\s*[\"\<](.*\/)?(.*)[\"\>]", text):
                includes.append(match_.group(2))

            if includes:
                assert not input_entry_path in table

                table[name] = {
                    "includes": includes,
                    "size": input_entry_path.stat().st_size,
                }

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

    table = get_header_table(args.input_directory_path)

    occurrences = count_occurrences(table)

    occurrences["meta"]["total_inclusions"] = sum(occurrences["counts"].values())

    occurrences["counts"] = dict(
        sorted(occurrences["counts"].items(), key=lambda item: item[1], reverse=True)
    )
    with open(args.output_occurrences_path, "w") as f:
        json.dump(occurrences, f)


if __name__ == "__main__":
    main()
