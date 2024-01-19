# includes_tabulator

This tool outputs a JSON file containing statistics about which headers were included the most often in your project, which files included the most headers, and so on.

I created this tool to help me diagnose compilation time issues in the [Cortex Command Community Project](https://github.com/cortex-command-community/Cortex-Command-Community-Project).

## Usage

Either launch the program in VS Code, which uses the `.vscode/launch.json` file, or run this command:

`python3.10 main.py tests occurrences.json`
