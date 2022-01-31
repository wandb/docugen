import configparser
from importlib import import_module
import operator
import os

import wandb

from docugen import doc_controls
from docugen import generate

import util

config = configparser.ConfigParser()
config_path = os.environ.get("DOCUGEN_CONFIG_PATH") or "./config.ini"
with open(config_path) as config_file:
    config_string = config_file.read()

    print('config file contains: \n', config_string)
    config.read_string(config_string)

DIRNAME = config["GLOBAL"]["DIRNAME"]
LIBRARY_DIRNAME = config["WANDB_CORE"]["dirname"]

subconfig_names = config["SUBCONFIGS"]["names"].split(",")

subconfigs = util.process_subconfigs(config, subconfig_names)

WANDB_CORE, WANDB_DATATYPES, WANDB_API, WANDB_INTEGRATIONS = subconfigs


def build(commit_id, code_url_prefix, output_dir):
    """Builds docs in stages: main library, then subcomponents."""
    configure_doc_hiding()

    output_dir = os.path.join(output_dir, DIRNAME)
    build_docs_from_config(WANDB_CORE, commit_id, code_url_prefix, output_dir)

    modules_output_dir = os.path.join(output_dir, LIBRARY_DIRNAME)
    build_docs_from_config(WANDB_DATATYPES, commit_id, code_url_prefix, modules_output_dir)
    build_docs_from_config(WANDB_API, commit_id, code_url_prefix, modules_output_dir)
    build_docs_from_config(WANDB_INTEGRATIONS, commit_id, code_url_prefix, modules_output_dir)


def build_docs_from_config(config, commit_id, code_url_prefix, output_dir):
    """Uses a config to build docs for a specific library component."""
    handle_additions(config["add-from"], config["add-elements"])
    wandb.__all__ = config["elements"] + config["add-elements"]

    wandb.__doc__ = get_dunder_doc(config["module-doc-from"])

    build_docs(
        name_pair=(config["dirname"], wandb),
        output_dir=output_dir,
        code_url_prefix=code_url_prefix,
    )


def build_docs(name_pair, output_dir, code_url_prefix):
    """Builds Python docs for W&B client library.

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


def handle_additions(add_from, add_elements):
    """Adds elements of a submodule of wandb to the top level."""
    if not add_from:
        return
    try:
        module = operator.attrgetter(add_from)(wandb)
    except AttributeError:  # if it's not an attribute, assume it needs to be imported
        module = import_module("." + add_from, "wandb")
    except ModuleNotFoundError as e:
        raise(e)
    for element in add_elements:
        setattr(wandb, element, getattr(module, element))


def get_dunder_doc(module_doc_from):
    """Fetches the __doc__ attribute from a module, or passes a default."""
    if module_doc_from == "":
        return """\n"""
    elif module_doc_from == "self":
        return wandb.__doc__
    else:
        doc_getter = operator.attrgetter(module_doc_from + "." + "__doc__")
        return doc_getter(wandb)


def configure_doc_hiding():
    """Uses doc_controls to hide certain classes and attributes."""
    deco = doc_controls.do_not_doc_in_subclasses

    # avoid documenting internal methods
    #  that are defined in basic datatypes and apis
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
