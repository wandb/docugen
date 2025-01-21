"""Generate reference documentation for Weights & Biases.

Creates docs for the Weights & Biases SDK library and for the wandb CLI tool.

For help, run:

python generate.py --help
"""
import argparse
import os
import shutil

import wandb

import cli
import library

import re


# Replace auto-generated title as a key, provide the preferred title as the value
MARKDOWN_TITLES = {
    "python": "Python Library",
    "data-types": "Data Types",
    "public-api": "Import & Export API",
    "integrations": "Integrations",
    "ref": "Reference",
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
    print("Building CLI....")
    cli.build(ref_dir)

    # change folders with single README to file.md
    single_folder_format(ref_dir)

    # clean up the file names
    clean_names(ref_dir)

    # Fix frontmatter
    reformat_title_to_frontmatter(ref_dir)

    # Rename README.md to _index.md
    reformat_and_rename_readme(ref_dir, title_mapping)


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
                # Format README doc titles to preferred title
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


def reformat_title_to_frontmatter(directory):
    "Fixes the title in the frontmatter of markdown files. Required for Hugo."
 
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):  # Only process markdown files
                file_path = os.path.join(root, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                if lines and lines[0].startswith("title:"):
                    # Reformat to markdown frontmatter
                    frontmatter = f"---\n{lines[0].strip()}\n---\n"

                    # Write back to the file with the updated format
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(frontmatter)
                        f.writelines(lines[1:])  # Write the rest of the file



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


def reformat_and_rename_readme(directory, title_mapping):
    for root, _, files in os.walk(directory):
        for file in files:
            if file == "README.md" or file == "_index.md":
                file_path = os.path.join(root, file)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Process the lines
                updated_lines = []
                for line in lines:
                    # Remove CTA buttons
                    if re.match(r"\{\{\<\s*cta-button.*?\>\}\}", line.strip()):
                        continue
                    
                    # Update the title
                    if line.startswith("title:"):
                        old_title = line[len("title:"):].strip()
                        # Check if the title is in the mapping
                        new_title = title_mapping.get(old_title, old_title.capitalize())
                        line = f"title: {new_title}\n"
                    
                    updated_lines.append(line)

                # Rename README.md to _index.md
                new_file_path = os.path.join(root, "_index.md")
                if file == "README.md":
                    os.rename(file_path, new_file_path)
                    file_path = new_file_path

                # Write back the updated file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(updated_lines)
                print(f"Processed: {file_path}")

# def reformat_and_rename_readme(directory, title_mapping):
#     for root, _, files in os.walk(directory):
#         for file in files:
#             if file == "README.md" or file == "_index.md":
#                 file_path = os.path.join(root, file)
                
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     lines = f.readlines()
                
#                 # Remove CTA buttons
#                 cleaned_lines = [
#                     line for line in lines 
#                     if not re.match(r"\{\{\<\s*cta-button.*?\>\}\}", line.strip())
#                 ]

#                 # Replace title values
#                 for i, line in enumerate(cleaned_lines):
#                     if line.strip().startswith("title:"):
#                         title_line = line.strip()
#                         old_title = title_line[len("title:"):].strip()
#                         # Remove quotes if present
#                         old_title = old_title.strip('"').strip("'")
#                         if old_title in title_mapping:
#                             new_title = title_mapping[old_title]
#                             cleaned_lines[i] = f"title: {new_title}\n"
#                         break  # Only process the first title

#                 # Rename README.md to _index.md
#                 new_file_path = os.path.join(root, "_index.md")
#                 if file == "README.md":
#                     os.rename(file_path, new_file_path)
#                     file_path = new_file_path
                
#                 # Write back the cleaned and updated file
#                 with open(file_path, "w", encoding="utf-8") as f:
#                     f.writelines(cleaned_lines)
#                 print(f"Processed: {file_path}")

title_mapping = {
    "python": "Python Library",
    "data-types": "Data Types",
    "integrations": "Integrations",
    "public-api": "Import & Export API",
}

def get_args():
    parser = argparse.ArgumentParser(
        description="Generate documentation for the wandb library and CLI."
    )
    # The commit_id can be the complete git hash
    # or can be the tag for the version of code.
    # eg. HASH = https://github.com/wandb/wandb/tree/c129c32964aca6a8509d98a0cc3c9bc46f2d8a4c
    # eg. TAG = https://github.com/wandb/wandb/tree/v0.15.5
    parser.add_argument(
        "--commit_id",
        type=str,
        help="Hash/Tag for the git commit to base the docs on. "
        + "Ensures that the source code is properly linked.",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="https://www.github.com/wandb/wandb",
        help="Repo to link for source code. Defaults to wandb/wandb.",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="wandb",
        help="Folder within GitHub repo where wandb SDK code is located. "
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
    main(get_args())
