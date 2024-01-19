import argparse
import json
import re
from pathlib import Path

hpp_exts = {".h", ".hh", ".hpp", ".h++"}
cpp_exts = {".c", ".cc", ".cpp", ".c++"}

cpp_and_hpp_exts = hpp_exts | cpp_exts

counts_filter_exts = {
    "sources": cpp_exts,
    "headers": hpp_exts,
    "both": cpp_and_hpp_exts,
}


def recursively_loop_hpp(table, include, seen):
    if include in seen:
        return
    seen.add(include)

    if include in table:
        for subinclude in table[include]["includes"]:
            recursively_loop_hpp(table, subinclude, seen)


def loop_hpp(table, including_counts):
    for name, value in table.items():
        includes = value["includes"]

        extension = Path(name).suffix
        if extension in hpp_exts:
            seen = set()
            for include in includes:
                recursively_loop_hpp(table, str(include), seen)

            assert not name in including_counts
            including_counts[name] = len(seen)


def recursively_loop_cpp(table, meta, inclusion_counts, include, seen):
    if include in seen:
        return
    seen.add(include)

    inclusion_counts[include] = inclusion_counts.get(include, 0) + 1

    if include in table:
        size = table[include]["size"]
        meta["total_included_bytes"] += size

        extension = Path(include).suffix
        if extension in hpp_exts:
            meta["total_included_hpp_bytes"] += size
        elif extension in cpp_exts:
            meta["total_included_cpp_bytes"] += size

        for subinclude in table[include]["includes"]:
            recursively_loop_cpp(table, meta, inclusion_counts, subinclude, seen)


def loop_cpp(table, meta, inclusion_counts, including_counts):
    for name, value in table.items():
        includes = value["includes"]

        extension = Path(name).suffix
        if extension in cpp_exts:
            size = value["size"]
            meta["total_included_bytes"] += size
            meta["total_included_cpp_bytes"] += size

            seen = set()
            for include in includes:
                recursively_loop_cpp(table, meta, inclusion_counts, str(include), seen)

            assert not name in including_counts
            including_counts[name] = len(seen)


def get_header_table(input_directory_path):
    table = {}

    for input_entry_path in input_directory_path.rglob("*"):
        name = input_entry_path.name

        extension = input_entry_path.suffix
        if extension in cpp_and_hpp_exts:
            # print(input_entry_path)

            # Cortex Command's files are jank, so the default encoding crashes this program
            text = input_entry_path.read_text(encoding="latin1")

            includes = []
            for match_ in re.finditer(r"#\s*include\s*[\"\<](.*\/)?(.*)[\"\>]", text):
                includes.append(match_.group(2))

            if includes:
                assert not name in table
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
    parser.add_argument(
        "--including_counts_filter",
        choices=["sources", "headers", "both"],
        default="both",
        help="Specific file type to filter 'including_counts' in the JSON file by",
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

    inclusion_counts = {}
    including_counts = {}

    loop_cpp(table, meta, inclusion_counts, including_counts)
    meta["total_inclusions"] = sum(inclusion_counts.values())
    inclusion_counts = dict(
        sorted(
            inclusion_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    loop_hpp(table, including_counts)
    meta["total_includings"] = sum(including_counts.values())
    including_counts = dict(
        sorted(
            including_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    counts_filter_ext = counts_filter_exts[args.including_counts_filter]
    including_counts = {
        name: v
        for name, v in including_counts.items()
        if Path(name).suffix in counts_filter_ext
    }

    chunkiness_scores = inclusion_counts.copy()
    for name in chunkiness_scores.keys():
        if name in including_counts:
            chunkiness_scores[name] *= including_counts[name]
    chunkiness_scores = dict(
        sorted(
            chunkiness_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    occurrences = {
        "meta": meta,
        "inclusion_counts": inclusion_counts,
        "including_counts": including_counts,
        "chunkiness_scores": chunkiness_scores,
    }
    with open(args.output_occurrences_path, "w") as f:
        json.dump(occurrences, f, indent=4)


if __name__ == "__main__":
    main()
