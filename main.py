import argparse
import json
import re
from pathlib import Path

hpp_ext = {".h", ".hh", ".hpp", ".h++"}
cpp_ext = {".c", ".cc", ".cpp", ".c++"}

cpp_and_hpp_ext = hpp_ext | cpp_ext


def recursively_get_including_counts(table, meta, including_counts, include, seen):
    # Check if we're in an infinite loop
    if include in seen:
        return 0

    count = 0

    if include in table:
        size = table[include]["size"]
        meta["total_included_bytes"] += size

        extension = Path(include).suffix
        if extension in hpp_ext:
            meta["total_included_hpp_bytes"] += size
        elif extension in cpp_ext:
            meta["total_included_cpp_bytes"] += size

        seen.append(include)
        for subinclude in table[include]["includes"]:
            count += recursively_get_including_counts(
                table, meta, including_counts, subinclude, seen
            )
        seen.pop()

    if count > 0:
        assert (not include in including_counts) or (including_counts[include] == count)
        including_counts[include] = count

    return count + 1


def get_including_counts(table, meta):
    including_counts = {}

    for name, value in table.items():
        includes = value["includes"]

        extension = Path(name).suffix
        if extension in cpp_ext:
            count = 0

            for include in includes:
                seen = []
                count += recursively_get_including_counts(
                    table, meta, including_counts, str(include), seen
                )

            if count > 0:
                assert (not name in including_counts) or (
                    including_counts[name] == count
                )
                including_counts[name] = count

    return including_counts


def recursively_get_inclusion_counts(table, meta, inclusion_counts, include, seen):
    # Check if we've already included this header in this cpp file
    if include in seen:
        return

    inclusion_counts[include] = inclusion_counts.get(include, 0) + 1

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
            recursively_get_inclusion_counts(
                table, meta, inclusion_counts, subinclude, seen
            )


def get_inclusion_counts(table, meta):
    inclusion_counts = {}

    for name, value in table.items():
        includes = value["includes"]

        extension = Path(name).suffix
        if extension in cpp_ext:
            size = value["size"]
            meta["total_included_bytes"] += size
            meta["total_included_cpp_bytes"] += size

            for include in includes:
                seen = set()
                recursively_get_inclusion_counts(
                    table, meta, inclusion_counts, str(include), seen
                )

    return inclusion_counts


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

    meta = {
        "total_included_bytes": 0,
        "total_included_hpp_bytes": 0,
        "total_included_cpp_bytes": 0,
    }

    inclusion_counts = get_inclusion_counts(table, meta)
    meta["total_inclusions"] = sum(inclusion_counts.values())
    inclusion_counts = dict(
        sorted(
            inclusion_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    including_counts = get_including_counts(table, meta)
    meta["total_includings"] = sum(including_counts.values())
    including_counts = dict(
        sorted(
            including_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    occurrences = {
        "meta": meta,
        "inclusion_counts": inclusion_counts,
        "including_counts": including_counts,
    }
    with open(args.output_occurrences_path, "w") as f:
        json.dump(occurrences, f)


if __name__ == "__main__":
    main()
