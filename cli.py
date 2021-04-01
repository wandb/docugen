import os
import re
import subprocess
from typing import Tuple

PATTERN = re.compile(r"(.*?\w) +(.*)")
# (           - Start of capture
#  .*?        - 0 or more repetitions of any character except a new line (non-greedy)
#   \w        - Not a word character
#      )      - End of capture
#       +     - 1 or more repetitions of space
#        (    - Start of capture
#         .*  - 0 of more repetitions of any character except a new line
#           ) - End of group

KEYWORDS = ["Options:", "Commands:"]
TEMPLATE = "# {}\n\n{}\n\n{}\n\n{}\n\n{}"


def build(output_dir: str = None):
    """
    Entry point for docgen_cli.

    Builds the entire documentation for `wandb` CLI
    by calling wandb --help, parsing the output,
    and then doing the same for each subcommand.

    Args:
        output_dir: (str) The output directory for the generated CLI docs.
    """
    if output_dir is None:
        output_dir = os.getcwd()

    output_dir, output_file = prepare_dirs(output_dir, "cli")

    markdown_render("wandb", output_dir, output_file)


def markdown_render(command: str, output_dir: str, output_file: str) -> str:
    """
    Renders the markdown and also provides
    the commands nested in it.

    Args:
        command: (str) The command that is executed as `wandb command --help`
        output_file: (str) The file in which the markdown is written.

    Returns:
        str: The output directory
    """
    usage, summary, parsed_dict = parse_help(command)
    if usage:
        # Document usage
        usage = usage.split(":")
        usage = f"**Usage**\n\n`{usage[1]}`"
    if summary:
        # Document summary
        summary = f"**Summary**\n{summary}"

    if "Options:" in parsed_dict.keys():
        options = get_options_markdown(parsed_dict["Options:"])
    else:
        options = ""

    if "Commands:" in parsed_dict.keys():
        subcommands, subcommand_list = get_subcommands_markdown(command, parsed_dict["Commands:"])
    else:
        subcommands, subcommand_list = "", []

    # Write to the output file
    if usage or summary or options or subcommands:
        write_to_file(output_file, command, usage, summary, options, subcommands)

    # render markdown for subcommands
    if len(subcommand_list) > 0:
        for command in subcommand_list:
            # For `command --help`
            command_dir_name = "-".join(command.split(" "))
            output_dir, output_file = prepare_dirs(output_dir, command_dir_name)

            output_dir = markdown_render(command, output_dir, output_file)

    parent_path = os.path.dirname(output_dir)

    return parent_path


def run_help(command: str) -> str:
    """
    Runs `command --help` and gathers the output.

    Args:
        command: (str) The command eg. wandb in `wandb --help`

    Returns:
        str: The help page of the command.
    """
    help_page = subprocess.run(
        f"{command} --help", shell=True, capture_output=True, text=True
    ).stdout
    return help_page


def parse_help(command: str) -> Tuple[str, str, str]:
    """
    Gathers the help page of the command and then parses it.

    It is noted that the help page is structured in the following manner.
    ```bash
    Usage: ....

    <Summary>

    Options:
    ...

    Commands:
    ...
    ```
    This help page is parsed in Usage, Summary and a Parsed Dict
    that contains Options and Commands.

    Args:
        command (str): The command eg. wandb in `wandb --help`

    Returns:
        str, str, str: usage, summary and the parsed document
    """
    help_page = run_help(command)
    summary = []
    keyword = None  # initializing keyword with None
    parsed_dict = {}  # will hold Options and Commands

    for line in help_page.split("\n"):
        line = line.strip()
        if line in KEYWORDS:  # Keywords contains [Options, Commands]
            parsed_dict[line] = []
            keyword = line
            continue
        if keyword is None:
            summary.append(line)
        else:
            # PATTERN help with option and value
            # eg --version Show the version
            # [("--version","Show the version")]
            extract = PATTERN.findall(line)
            if extract:
                parsed_dict[keyword].append([extract[0][0], extract[0][1]])

    if len(summary) == 0:
        return "", "", parsed_dict
    elif len(summary) == 1:
        return summary[0], "", parsed_dict
    else:
        usage = summary[0]
        summary = "\n".join(summary[1:])
        return usage, summary, parsed_dict


def get_options_markdown(options):
    """Formats the options of a command as a markdown table.
    """
    options_md = ""

    for element in options:
        description = parse_description(element)

        # concatenate all the options
        options_md += f"""|{element[0]}|{description}|\n"""

    options_md = (
        """**Options**\n| **Options** | **Description** |\n|:--|:--|:--|\n"""
        + options_md
    )
    return options_md


def get_subcommands_markdown(command, subcommands):
    """Formats the subcommands of a command as a markdown table.
    """
    subcommands_md, subcommand_list = "", []

    for element in subcommands:
        subcommand_list.append(
            f"{command} {element[0]}"
        )  # Keeping a list of all the nested counts
        description = parse_description(element)
        # concatenate all the options
        subcommands_md += f"""|{element[0]}|{description}|\n"""
    subcommands_md = (
        """**Commands**\n| **Commands** | **Description** |\n|:--|:--|:--|\n"""
        + subcommands_md
    )

    return subcommands_md, subcommand_list


def parse_description(element):

    markdown = (
        " ".join(list(filter(lambda x: x, element[1].split(" ")[1:])))
        if element[1]
        .split(" ")[0]
        .isupper()  # to check for types in help page eg. --version INTEGER the version
        else element[1]
    )

    return markdown


def write_to_file(output_file, command, usage, summary, options, subcommands):
    """Write contents to the output_file based on TEMPLATE"""

    contents = TEMPLATE.format(command, usage, summary, options, subcommands)
    with open(output_file, "w") as fp:
        fp.write(contents)


def prepare_dirs(base_dir, subdir_name):
    """Add a subdirectory with README to a base directory.

    Returns the directory and README paths.
    """
    subdir = os.path.join(base_dir, subdir_name)
    os.mkdir(path=subdir)
    markdown_file = os.path.join(subdir, "README.md")
    return subdir, markdown_file
