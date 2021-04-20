import os

from docugen import doc_controls
from docugen import generate
import wandb

DIRNAME = "ref"
LIBRARY_DIRNAME = "python"

# fmt: off
# which datatypes are we documenting?
WANDB_DATATYPES = ["Graph", "Image", "Plotly", "Video",
                   "Audio", "Table", "Html", "Object3D",
                   "Molecule", "Histogram",]

# which parts of the API are we documenting?
WANDB_API = ["Api", "Projects", "Project", "Runs", "Run",
             "Sweep", "Files", "File", "Artifact",]
# fmt: on

# later, we'll decide which parts of the sdk we're documenting
WANDB_DOCLIST = []


def build(git_hash, code_url_prefix, output_dir):
    """Builds docs in three stages: library, data types, and API.

    For now, this involves a lot of special-casing.
    """

    configure_doc_hiding()

    # each of these operates by changing the __all__
    #  attribute of the wandb module, populating it with
    #  the relevant objects and then generating docs.

    build_library_docs(git_hash, code_url_prefix, output_dir)
    build_datatype_docs(git_hash, code_url_prefix, output_dir)
    build_api_docs(git_hash, code_url_prefix, output_dir)


def build_docs(name_pair, output_dir, code_url_prefix):
    """Build api docs for W&B.

    Args:
        name_pair: Name of the pymodule
        output_dir: A string path, where to put the files.
        code_url_prefix: prefix for "Defined in" links.
        search_hints: Bool. Include meta-data search hints at the top of each file.
        gen_report: Bool. Generates an API report containing the health of the
            docstrings of the public API.
    """

    doc_generator = generate.DocGenerator(
        root_title="W&B",
        py_modules=[name_pair],
        base_dir=os.path.dirname(wandb.__file__),
        code_url_prefix=code_url_prefix,
    )

    doc_generator.build(output_dir)


def build_library_docs(git_hash, code_url_prefix, output_dir):
    # we start from the current __all__ attribute
    doclist = wandb.__all__

    # the datatypes are included at the top level,
    #  but maybe should not be?
    doclist = [elem for elem in doclist if elem not in WANDB_DATATYPES]

    # some parts of the Api are included at the top level,
    #  but maybe should not be?
    doclist = [elem for elem in doclist if elem not in WANDB_API]

    # add back in Artifact, which is also an object in the API
    doclist.append("Artifact")

    # the "Run" object is not included at the top level,
    #  but maybe it should be?
    #  instead, there's a lower-case .run at the top level
    #  also needs to be added back, since there's a Run in the API
    wandb.Run = wandb.wandb_sdk.wandb_run.Run
    doclist.extend(["Run"])

    # for now, remove .join and document .finish
    doclist.extend(["finish"])
    doclist = [elem for elem in doclist if elem != "join"]

    WANDB_DOCLIST.extend(doclist)

    wandb.__all__ = doclist
    wandb.__doc__ = """\n"""

    build_docs(
        name_pair=(LIBRARY_DIRNAME, wandb),
        output_dir=os.path.join(output_dir, DIRNAME),
        code_url_prefix=code_url_prefix,
    )


def build_datatype_docs(git_hash, code_url_prefix, output_dir):

    wandb.__all__ = WANDB_DATATYPES
    wandb.__doc__ = """\n"""

    build_docs(
        name_pair=("data-types", wandb),
        output_dir=os.path.join(output_dir, DIRNAME, LIBRARY_DIRNAME),
        code_url_prefix=code_url_prefix,
    )


def build_api_docs(git_hash, code_url_prefix, output_dir):

    # this should be made cleaner
    #  by either using the __all__ of the api
    #  or changing the top-level __all__

    wandb.Api = wandb.apis.public.Api
    wandb.Projects = wandb.apis.public.Projects
    wandb.Project = wandb.apis.public.Project
    wandb.Runs = wandb.apis.public.Runs
    wandb.Run = wandb.apis.public.Run
    wandb.Sweep = wandb.apis.public.Sweep
    wandb.Files = wandb.apis.public.Files
    wandb.File = wandb.apis.public.File
    wandb.Artifact = wandb.apis.public.Artifact

    wandb.__all__ = WANDB_API
    wandb.__doc__ = """
    Use the Public API to export or update data that you have saved to W&B.
    Before using this API, you'll want to log data from your script — check the [Quickstart](../quickstart.md) for more details.

    **Use Cases for the Public API**

    * **Export Data**: Pull down a dataframe for custom analysis in a Jupyter Notebook. Once you have explored the data, you can sync your findings by creating a new analysis run and logging results, for example: `wandb.init(job_type="analysis")`
    * **Update Existing Runs**: You can update the data logged in association with a W&B run. For example, you might want to update the config of a set of runs to include additional information, like the architecture or a hyperparameter that wasn't originally logged.

    See the [Generated Reference Docs](../ref/public-api/) for details on available functions.
    """

    build_docs(
        name_pair=("public-api", wandb),
        output_dir=os.path.join(output_dir, DIRNAME, LIBRARY_DIRNAME),
        code_url_prefix=code_url_prefix,
    )


def configure_doc_hiding():

    # avoid documenting internal methods
    #  that are defined in basic datatypes and apis

    deco = doc_controls.do_not_doc_in_subclasses
    base_classes = [
        wandb.data_types.WBValue,
        wandb.data_types.Media,
        wandb.data_types.BatchableMedia,
        wandb.apis.public.Paginator,
    ]

    for cls in base_classes:
        doc_controls.decorate_all_class_attributes(
            decorator=deco, cls=cls, skip=["__init__"]
        )
