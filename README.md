# Documentation Generation

## `generate.py`

This script generates documentation for the `wandb` SDK library.

For help with this function, run

```shell
python generate.py --help
```

It uses a more generic documentation generation tool,
`docugen`,
based on the
[TensorFlow documentation generator](https://www.github.com/tensorflow/docs).

### Steps

1. Run `pip install --upgrade git+git://github.com/wandb/wandb.git@<commit_id>`
   to install the version of`wandb` you wish to document.
2. Run `python generate.py --commit_id <commit_id>` to create the documentation.
   Make sure to use a full hash or tag -- it's used to create URLs.
3. Move the generated documentation into a local copy
   of the Docs repository (under `docs/ref`).

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

```shell
python generate.py \
  --template_file _SUMMARY.md \
  --commit_id v0.15.6 \
  --output_dir path/to/gitbook
```

### Requirements

Run `pip install -r docugen/requirements.txt` from root to install requirements.

## Extension and `config`uration

Behavior is configured by the `config.ini` file,
which is loaded using `ConfigParser`.

To extend the footprint of the library that is documented,
this file must be edited.

There's a rough dummy/documentary example in `config.ini`, the `EXAMPLE_SUBCONFIG`.

**If the newly-documented components are in the top level of a module that is already being documented**,
e.g. if a method is added to the top-level `wandb` or if a new `data_type` is added to `wandb.data_types`,
then add the `elements` to document to either `elements` or `add-elements` in the proper `SUBCONFIG`.

For example, if we added `launch` as a method available at `wandb.launch` and wanted to document it
at the top level (alongside e.g. `wandb.watch`), we'd add it to the `elements` of the `WANDB_CORE` subconfig.

As another example, if we added `PanopticSegmentation` to the `wandb.data_types` submodule,
but didn't make it available at the top level, we'd add it to the `add-elements` section of the `WANDB_DATATYPES` subconfig.

Editing on top of [the state at commit `7ab1d97`](https://github.com/wandb/docugen/blob/7ab1d97cb504d502a665464635e3e247bb9859c1/config.ini), the subconfig sections of `config.ini` would look like:

```ini
[WANDB_CORE]
# main python SDK library
dirname=python
title=Python Library
slug=wandb.
elements=Artifact,agent,config,controller,finish,init,launch,log,save,summary,sweep,watch,__version__
add-from=wandb_sdk.wandb_run
add-elements=Run
module-doc-from=self

[WANDB_DATATYPES]
# data types submodule, including media and tables
dirname=data-types
title=Data Types
slug=wandb.data\_types.
elements=Graph,Image,Plotly,Video,Audio,Table,Html,Object3D,Molecule,Histogram
add-from=data_types
add-elements=ImageMask,BoundingBoxes2D,PanopticSegmentation
module-doc-from=data_types
```

**If the newly-documented components are not in the top level of a module that is already being documented**,
then you'll need to add a new section to the reference docs (though it'd be easier just export them at the top level and add them to an existing section!).

You'll need to

1. Add a new subconfig, a la `WANDB_DATATYPES`
2. Populate that with all the required tags (see `EXAMPLE_SUBCONFIG`)
3. Add that subconfig to the `SUB_CONFIGS`
4. Add handling for the new section to `generate.py`, under `get_prefix`
5. Add handling for the new section to `library.py`, under `build`. (This last step could probably be easily automated away with some slight changes to the logic there).

## Running as a GitHub Action

In any wandb repo's Actions workflow, you can trigger document generation like so...

```yml
- uses: wandb/docugen@vX.Y.Z
  with:
    gitbook-branch: en
    access-token: ${{ secrets.DOCUGEN_ACCESS_TOKEN }}
```

where `vX.Y.Z` is a tag on this (docugen) repo and `DOCUGEN_ACCESS_TOKEN` is a Personal Access Token with org write permissions, stored in the consuming repo. This will generate docs based on the latest releases of all contributing projects and push them to the target branch in the gitbook repo (`en` is the branch used for the main English docs).

### Updating the GitHub Action

After merging your changes to `docugen@main`...

```bash
git tag -a vX.Y.Z -m "docugen version X.Y.Z"
git push origin vX.Y.Z
```

Then you'll need to update the `uses` line in the consuming repo. If we eventually have a lot of repos doing this it might be better to refer to `@main`, to save us the trouble of manually updating all of them (note that if you don't update a repo, it will trigger the old document generation logic, potentially overwriting new docs).

You can test changes to the action on a branch with `uses: wandb/docugen@branch-name` from any other repo.
