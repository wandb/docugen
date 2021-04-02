"""A tool to generate reference documentation for the
Weights & Biases client library and for the wandb CLI tool.

For help, run:

python generate.py --help
"""
import argparse
import os
from pathlib import Path

import cli
import library

DIRNAME = library.DIRNAME  # directory name for autodocs

DIRNAMES_TO_TITLES = {
    DIRNAME: "Reference Docs",
    "cli": "Command Line Interface",
    "data-types": "Data Types",
    "public-api": "Import & Export API",
}


def main(args):
    git_hash = args.git_hash
    output_dir = args.output_dir
    template_file = args.template_file

    code_url_prefix = "/".join([args.repo, "tree", f"{git_hash}", args.prefix])

    # Create the library docs
    library.build(git_hash, code_url_prefix, output_dir)

    # convert .build output to GitBook format
    rename_to_readme(output_dir)
    library_dir = os.path.join(output_dir, DIRNAME)
    clean_names(library_dir)

    # Create the CLI docs
    cli.build(library_dir)

    # fill the SUMMARY.md with generated doc files,
    #  based on provided template.
    populate_summary(library_dir, template_file, output_dir=output_dir)


def populate_summary(
    docgen_folder: str, template_file: str = "_SUMMARY.md", output_dir: str = "."
) -> None:
    """Populates the output file with generated file names
    by filling in the template_file at the {autodoc} location.

    GitBook uses a `SUMMARY.md` file to determine which
    files to show in the sidebar. When using autodoc,
    we must generate this partly programmatically.

    Args:
        docgen_folder: str. The root folder that contains
            the generated docs.
        template_file: str. A markdown template that contains
            the rest of the SUMMARY.md.
        output_dir: str. Directory into which to write the final
            SUMMARY.md file.
    """

    with open(template_file, "r") as f:
        doc_structure = f.read()

    autodoc_markdown = walk_autodoc(docgen_folder)

    doc_structure = doc_structure.format(autodoc=autodoc_markdown)

    with open(os.path.join(output_dir, "SUMMARY.md"), "w") as f:
        f.write(doc_structure)


def walk_autodoc(folder: str) -> str:
    """Walks a folder, pulls out all of the markdown files,
    formats their names into markdown strings with appropriate links
    and formatting for a GitBook SUMMARY.md, then returns that block of markdown.
    """

    autodoc_markdowns = []
    indent = 0
    for path, dirs, files in os.walk(folder):
        dirs.sort()
        files.sort()
        path = str(Path(path).relative_to(Path(folder).parent))
        is_subdir = "/" in path
        if is_subdir:
            components = path.split("/")
            indent = len(components)
            name = components[-1]
        else:
            name = path
        title = convert_name(name)
        autodoc_markdowns.append("  " * indent + f"* [{title}]({path}/README.md)")

        autodoc_markdowns.extend(add_files(files, path, indent))

    autodoc_markdown = "\n".join(autodoc_markdowns)

    return autodoc_markdown


def add_files(files: list, root: str, indent: int) -> list:
    file_markdowns = []
    indentation = "  " * indent
    for file_name in files:
        if file_name == "README.md" or not file_name.endswith(".md"):
            continue
        short_name = file_name.split(".")[0]
        source = infer_source(root)
        if short_name.title() in source:
            short_name = short_name.title()

        file_markdown = indentation + f"  * [{short_name}]({root}/{file_name})"
        file_markdowns.append(file_markdown)

    return file_markdowns


def infer_source(path):
    if path == DIRNAME:
        return library.WANDB_DOCLIST
    elif "data-types" in path:
        return library.WANDB_DATATYPES
    elif "public-api" in path:
        return library.WANDB_API
    else:
        return []


def convert_name(name):
    if name in DIRNAMES_TO_TITLES.keys():
        name = DIRNAMES_TO_TITLES[name]

    name = name.replace("-", " ")

    return name


def rename_to_readme(directory):
    """Moves all the folder-level markdown files into
    their respective folders, as a README."""

    for root, folders, file_names in os.walk(directory):
        for file_name in file_names:
            raw_file_name, suffix = file_name[:-3], file_name[-3:]
            if suffix == ".md" and raw_file_name in folders:
                os.rename(
                    os.path.join(f"{root}", file_name),
                    os.path.join(f"{root}", raw_file_name, "README.md"),
                )


def clean_names(directory):
    """Converts names to lower case and removes spaces"""
    for root, folders, file_names in os.walk(directory):
        for name in file_names:
            if name == "README.md":
                short_name = name
            else:
                short_name = name.replace(" ", "-").lower()
            os.rename(
                os.path.join(f"{root}", f"{name}"),
                os.path.join(f"{root}", f"{short_name}"),
            )


def filter_files(directory, files_to_remove):
    """Remove any unwanted files."""
    for root, _, file_names in os.walk(directory):
        for file_name in file_names:
            if file_name in files_to_remove:
                os.remove(os.path.join(f"{root}", f"{file_name}"))


def get_args():
    parser = argparse.ArgumentParser(
        description="Generate documentation for the wandb library and CLI."
    )
    parser.add_argument(
        "--git_hash",
        type=str,
        help="Hash for the git commit to base the docs on. "
        + "Ensures that the source code is properly linked.",
    )
    parser.add_argument(
        "--template_file",
        type=str,
        default="_SUMMARY.md",
        help="Template markdown file with {autodoc} where filenames to be written. "
        + "Defaults to _SUMMARY.md",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="https://www.github.com/wandb/client",
        help="Repo to link for source code. Defaults to wandb/client.",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="wandb",
        help="Folder within GitHUb repo where wandb client code is located. "
        + "Defaults to wandb.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.getcwd(),
        help=f"Folder into which to place folder {DIRNAME}/ containing results. "
        + "Defaults to current directory.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    main(args)
