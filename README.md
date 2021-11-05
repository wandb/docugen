# Documentation Generation

## `generate.py`

This script generates documentation for the `wandb` library
in a format suitable for use with GitBook.

For help with this function, run

```text
python generate.py --help
```

It uses a more generic documentation generation tool,
`docugen`,
based on the
[TensorFlow documentation generator](https://www.github.com/tensorflow/docs).

### Steps

1. Run `pip install --upgrade git+git://github.com/wandb/client.git@<commit_id>`
to install the version of`wandb` you wish to document.
2. Run `python generate.py --commit_id <commit_id>` to create the documentation.
Make sure to use a full hash or tag -- it's used to create URLs.
3. Move the generated documentation into a local copy of
[the repository for the GitBook](https://www.github.com/).

### Outputs

1. A folder named `ref`.
The files in the `ref` folder are the generated markdown.
Use the `--output_dir` option to change where this folder is saved;
by default it is in the working directory.
If the `output_dir` already contains a folder named `ref`,
any contents inside the `cli` or `python` directory will be over-written.
2. A `SUMMARY.md` file for creating a
[GitBook sidebar](https://docs.gitbook.com/integrations/github/content-configuration#summary)
that indexes the automatically-generated docs.
This is based on a provided `--template_file`
\(by default, `_SUMMARY.md` from this repo\).

### Example Usage

```python
python generate.py \
  --template_file _SUMMARY.md \
  --commit_id v0.10.28 \
  --output_dir path/to/gitbook
```

### Requirements

Run `pip install -r docugen/requirements.txt` from root to install requirements.
