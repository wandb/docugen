"""Generate reference documentation for Weights & Biases.

Creates docs for the Weights & Biases client library and for the wandb CLI tool.

For help, run:

python generate.py --help
"""
import argparse
import os
import shutil

import wandb

import cli
import library


# Replace auto-generated title as a key, provide the preferred title as the value
MARKDOWN_TITLES = {
    "python": "Python Library",
    "data-types": "Data Types",
    "public-api": "Import & Export API",
    "integrations": "Integrations",
    "ref": "Reference",
    "java": "Java Library [Beta]",
    "keras": "Keras",
    "weave": "Weave",
}


def main(args):
    commit_id = args.commit_id

    # check valid commit id
    check_commit_id(commit_id)

    output_dir = args.output_dir
    # template_file = args.template_file

    code_url_prefix = "/".join([args.repo, "tree", f"{commit_id}", args.prefix])

    ref_dir = os.path.join(output_dir, library.DIRNAME)
    for library.dirname in library.DIRNAMES_TO_TITLES.keys():
        if library.dirname in library.SKIPS or library.dirname in library.EXTERNAL:
            continue
        shutil.rmtree(os.path.join(ref_dir, library.dirname), ignore_errors=True)

    # create the library docs
    library.build(commit_id, code_url_prefix, output_dir)

    # convert .build output to a format docodile can use
    rename_to_readme(ref_dir)

    # create the CLI docs
    cli.build(ref_dir)

    # change folders with single README to file.md
    single_folder_format(ref_dir)

    # clean up the file names
    clean_names(ref_dir)


def rename_to_readme(directory):
    """Moves all folder-level markdown files into respective folders, as a README."""
    for root, folders, file_names in os.walk(directory):
        for file_name in file_names:
            raw_file_name, suffix = file_name[:-3], file_name[-3:]
            if suffix == ".md" and raw_file_name in folders:
                os.rename(
                    os.path.join(f"{root}", file_name),
                    os.path.join(f"{root}", raw_file_name, "README.md"),
                )
                # Format README doc titles to perferred title
                library.format_readme_titles(
                    os.path.join(f"{root}", raw_file_name, "README.md"), MARKDOWN_TITLES
                )


def clean_names(directory):
    """Converts names to lower case and removes spaces."""
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


def single_folder_format(directory):
    """Converts all sub-folders that only contain README.md to single files.

    So the tree:
        - folder
            - README.md

    changes to
        - folder.md

    Args:
        directory: str. The directory to walk through.
    """
    for root, folders, file_names in os.walk(directory):
        number_of_folders = len(folders)
        number_of_files = len(file_names)
        if number_of_folders == 0 and number_of_files == 1:
            if file_names[0] == "README.md":
                cwd = os.path.split(root)[-1]
                parent_root = os.path.abspath(os.path.join(root, ".."))
                os.rename(
                    os.path.join(f"{root}", "README.md"),
                    os.path.join(f"{parent_root}", f"{cwd}.md"),
                )
                os.rmdir(root)


def get_args():
    parser = argparse.ArgumentParser(
        description="Generate documentation for the wandb library and CLI."
    )
    # The commit_id can be the complete git hash
    # or can be the tag for the version of code.
    # eg. HASH = https://github.com/wandb/client/tree/c129c32964aca6a8509d98a0cc3c9bc46f2d8a4c
    # eg. TAG = https://github.com/wandb/client/tree/v0.10.27
    parser.add_argument(
        "--commit_id",
        type=str,
        help="Hash/Tag for the git commit to base the docs on. "
        + "Ensures that the source code is properly linked.",
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
        help="Folder within GitHub repo where wandb client code is located. "
        + "Defaults to wandb.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.getcwd(),
        help="Folder into which to place folder "
        "{library.DIRNAME}/ containing results. " + "Defaults to current directory.",
    )
    return parser.parse_args()


def check_commit_id(commit_id):
    """Checks for a valid commit id.

    Args:
        commit_id: The commit id provided
    """
    if commit_id == "latest":
        # using latest version instead of a commit id -- this should work as long as
        # we aren't hosting legacy doc versions -- if we do, we'll need to go back
        # to passing an actual id
        pass
    elif "." in commit_id:
        # commit_id is a version
        wandb_version = f"v{wandb.__version__}"
        assert (
            wandb_version == commit_id
        ), f"git version {commit_id} does not match wandb version {wandb_version}"
    else:
        # commit_id is a git hash
        commit_id_len = len(commit_id)
        assert (
            commit_id_len == 40
        ), f"git hash must have all 40 characters, was {commit_id}"


if __name__ == "__main__":
    args = get_args()
    main(args)
