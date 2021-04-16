import os
import re
import subprocess
from typing import Tuple

PATTERN = re.compile(r"(.*?)  +(.*)")
# (           - Start of capture
#  .*?        - 0 or more repetitions of any character except a new line (non-greedy)
#     )       - End of capture
#        +    - 2 or more repetitions of space
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
        subcommands, subcommand_list = get_subcommands_markdown(
            command, parsed_dict["Commands:"]
        )
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

    help_page = pre_process(help_page)

    for line in help_page.split("\n"):
        line = line.strip()
        if line in KEYWORDS:  # Keywords contains [Options, Commands]
            parsed_dict[line] = []
            keyword = line
            continue
        if keyword is None:
            summary.append(line)
        else:
            # PATTERN helps with option and value
            # eg. --version Shows the version
            # will be captured like
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


def pre_process(help_page: str) -> str:
    """
    This method is used to transform
    the help_page into a good format
    for the parser to parse it better.

    Args:
        help_page: The whole help page of a command

    Returns:
        str: The transformed help page.
    """
    re_space = re.compile(r"(^\s+)")  # To compute the starting space
    page_splits = help_page.split("\n")
    # if page_splits[0] == 'Usage: wandb docker [OPTIONS] [DOCKER_RUN_ARGS]... [DOCKER_IMAGE]':
    for idx, line in enumerate(page_splits):
        white_space = re_space.findall(line)
        if (white_space) and (len(white_space[0]) > 2):
            # Can be either a wrapped description
            # or a new description all together.
            if len(page_splits) >= idx + 1 and page_splits[idx + 1] == "":
                # wrapped description
                page_splits[idx - 1] = (
                    page_splits[idx - 1] + " " + page_splits.pop(idx).strip()
                )
                page_splits.pop(idx)
            else:
                # new description
                page_splits[idx - 1] = (
                    page_splits[idx - 1] + "   " + page_splits.pop(idx).strip()
                )
    return "\n".join(page_splits)


def get_options_markdown(options):
    """Formats the options of a command as a markdown table."""
    options_md = ""

    for element in options:
        arg = parse_description(element)
        desc = element[1]
        # concatenate all the options
        options_md += f"""|{arg}|{desc}|\n"""

    options_md = (
        """**Options**\n| **Options** | **Description** |\n|:--|:--|:--|\n"""
        + options_md
    )
    return options_md


def get_subcommands_markdown(command, subcommands):
    """Formats the subcommands of a command as a markdown table."""
    subcommands_md, subcommand_list = "", []

    for element in subcommands:
        subcommand_list.append(
            f"{command} {element[0]}"
        )  # Keeping a list of all the nested counts
        arg = parse_description(element)
        desc = element[1]
        # concatenate all the options
        subcommands_md += f"""|{arg}|{desc}|\n"""
    subcommands_md = (
        """**Commands**\n| **Commands** | **Description** |\n|:--|:--|:--|\n"""
        + subcommands_md
    )

    return subcommands_md, subcommand_list


def parse_description(element):

    markdown = " ".join(
        list(filter(lambda x: "" if x.isupper() else x, element[0].split(" ")))
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
