import configparser
import operator
import os

import wandb

from docugen import doc_controls
from docugen import generate

config = configparser.ConfigParser()
config.read("config.ini")

DIRNAME = config["GLOBAL"]["DIRNAME"]
LIBRARY_DIRNAME = config["WANDB_CORE"]["dirname"]

subconfig_names = config["SUBCONFIGS"]["names"].split(",")


def process_subconfigs(config, subconfig_names):
    subconfigs = []
    for name in subconfig_names:
        subconfig = dict(config[name])
        subconfig["add-elements"] = subconfig["add-elements"].split(",")
        subconfig["elements"] = subconfig["elements"].split(",")
        subconfigs.append(subconfig)
    return subconfigs


subconfigs = process_subconfigs(config, subconfig_names)

WANDB_CORE, WANDB_DATATYPES, WANDB_API, WANDB_INTEGRATIONS = subconfigs


def build(commit_id, code_url_prefix, output_dir):
    """Builds docs in stages: main library, then subcomponents."""
    configure_doc_hiding()

    # each of these operates by changing the __all__
    #  attribute of the wandb module, populating it with
    #  the relevant objects and then generating docs.

    build_library_docs(commit_id, code_url_prefix, output_dir)
    build_datatype_docs(commit_id, code_url_prefix, output_dir)
    build_api_docs(commit_id, code_url_prefix, output_dir)
    build_integration_docs(commit_id, code_url_prefix, output_dir)


def build_docs(name_pair, output_dir, code_url_prefix):
    """Builds api docs for W&B.

    Args:
        name_pair: Name of the pymodule
        output_dir: A string path, where to put the files.
        code_url_prefix: prefix for "Defined in" links.
    """
    doc_generator = generate.DocGenerator(
        root_title="W&B",
        py_modules=[name_pair],
        base_dir=os.path.dirname(wandb.__file__),
        code_url_prefix=code_url_prefix,
    )

    doc_generator.build(output_dir)


def build_library_docs(commit_id, code_url_prefix, output_dir):

    config = WANDB_CORE
    handle_additions(config["add-from"], config["add-elements"])
    wandb.__all__ = config["elements"] + config["add-elements"]

    wandb.__doc__ = """\n"""

    build_docs(
        name_pair=(config["dirname"], wandb),
        output_dir=os.path.join(output_dir, DIRNAME),
        code_url_prefix=code_url_prefix,
    )


def build_datatype_docs(commit_id, code_url_prefix, output_dir):

    config = WANDB_DATATYPES
    handle_additions(config["add-from"], config["add-elements"])
    wandb.__all__ = config["elements"] + config["add-elements"]

    # handle_additions("data_types", WANDB_DATATYPES["add-elements"])
    # wandb.__all__ = WANDB_DATATYPES["elements"] + WANDB_DATATYPES["add-elements"]
    wandb.__doc__ = """\n"""

    build_docs(
        name_pair=(config["dirname"], wandb),
        output_dir=os.path.join(output_dir, DIRNAME, LIBRARY_DIRNAME),
        code_url_prefix=code_url_prefix,
    )


def build_api_docs(commit_id, code_url_prefix, output_dir):

    # this should be made cleaner
    #  by either using the __all__ of the api
    #  or changing the top-level __all__

    config = WANDB_API
    handle_additions(config["add-from"], config["add-elements"])
    wandb.__all__ = config["elements"] + config["add-elements"]

    wandb.__doc__ = """
    Use the Public API to export or update data that you have saved to W&B.
    Before using this API, you'll want to log data from your script — check the [Quickstart](https://docs.wandb.ai/quickstart) for more details.

    **Use Cases for the Public API**

    * **Export Data**: Pull down a dataframe for custom analysis in a Jupyter Notebook. Once you have explored the data, you can sync your findings by creating a new analysis run and logging results, for example: `wandb.init(job_type="analysis")`
    * **Update Existing Runs**: You can update the data logged in association with a W&B run. For example, you might want to update the config of a set of runs to include additional information, like the architecture or a hyperparameter that wasn't originally logged.

    See the [Generated Reference Docs](https://docs.wandb.ai/ref) for details on available functions.
    """

    build_docs(
        name_pair=(config["dirname"], wandb),
        output_dir=os.path.join(output_dir, DIRNAME, LIBRARY_DIRNAME),
        code_url_prefix=code_url_prefix,
    )


def build_integration_docs(commit_id, code_url_prefix, output_dir):
    config = WANDB_INTEGRATIONS
    handle_additions(config["add-from"], config["add-elements"])
    wandb.__all__ = config["elements"] + config["add-elements"]

    wandb.__doc__ = """\n"""

    build_docs(
        name_pair=(config["dirname"], wandb),
        output_dir=os.path.join(output_dir, DIRNAME, LIBRARY_DIRNAME),
        code_url_prefix=code_url_prefix,
    )


def handle_additions(add_from, add_elements):
    if not add_from:
        return
    module = operator.attrgetter(add_from)(wandb)
    for element in add_elements:
        setattr(wandb, element, getattr(module, element))


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

    from tensorflow import keras
    deco = doc_controls.do_not_doc_in_subclasses
    doc_controls.decorate_all_class_attributes(
        decorator=deco, cls=keras.callbacks.Callback, skip=["__init__", "set_model", "set_params"])
