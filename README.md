# includes_tabulator

This tool outputs a JSON file containing statistics about which headers were included the most often in your project, which files included the most headers, and so on.

I created this tool to help me diagnose compilation time issues in the [Cortex Command Community Project](https://github.com/cortex-command-community/Cortex-Command-Community-Project).

## Usage

Either launch the program in VS Code, which uses the `.vscode/launch.json` file, or run this command:

`python3.10 main.py tests occurrences.json`

Run `python3.10 main.py --help` to get an explanation of the arguments.

## JSON explanation

### meta

Higher-level stats, which include summations of the other JSON keys.

### inclusion_counts

How often a header is included.

### including_counts

How many headers this header (indirectly) includes.

### chunkiness_scores

`chunkiness_score` is the `inclusion_count * including_count`

So this is saying that GUI.h is the most important header to optimize:

![Showing the chunkiness scores, where GUI.h has a score of 3444](chunkiness_scores.png)
