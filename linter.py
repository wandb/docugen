"""
This file holds the logic of linting.
"""
import os
import inspect
import wandb
import yaml

# LOAD YAML CONFIG
yaml_filename = 'config.yaml'
with open(yaml_filename) as yaml_file:
    p_yaml_file = yaml.load(yaml_file, Loader=yaml.FullLoader)

WANDB_DATATYPES = p_yaml_file["WANDB_DATATYPES"]
WANDB_API = p_yaml_file["WANDB_API"]
WANDB_INTEGRATIONS = p_yaml_file["WANDB_INTEGRATIONS"]

WANDB_FILENAME = []


def get_library_files():
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

    # remove .setup as it is not public
    doclist = [elem for elem in doclist if elem != "setup"]

    # adding `wandb.watch` to the doclist. The idea behind
    # adding watch to the parent docs and not integration
    # is that watch does not have a submodule namespace.
    doclist.extend(["watch"])
    wandb.__all__ = doclist
    wandb_all = [wandb.__dict__[w] for w in wandb.__all__]
    wandb_all.remove(wandb.__version__)
    WANDB_FILENAME.extend([inspect.getfile(wa) for wa in wandb_all])


def get_datatype_files():

    wandb.__all__ = WANDB_DATATYPES
    wandb_all = [wandb.__dict__[w] for w in wandb.__all__]
    WANDB_FILENAME.extend([inspect.getfile(wa) for wa in wandb_all])


def get_api_files():

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
    wandb_all = [wandb.__dict__[w] for w in wandb.__all__]
    WANDB_FILENAME.extend([inspect.getfile(wa) for wa in wandb_all])


def get_integration_files():
    # from wandb.integration import torch
    # from wandb.integration import sagemaker
    # from wandb.integration import fastai
    # wandb.torch = torch
    # wandb.sagemaker = sagemaker
    # wandb.fastai = fastai
    from wandb.integration import keras as wandb_keras
    wandb.keras = wandb_keras

    wandb.__all__ = WANDB_INTEGRATIONS
    wandb_all = [wandb.__dict__[w] for w in wandb.__all__]
    WANDB_FILENAME.extend([inspect.getfile(wa) for wa in wandb_all])


if __name__ == "__main__":
    get_library_files()
    get_datatype_files()
    get_api_files()
    get_integration_files()
    wandb_files = set(WANDB_FILENAME)
    # lint with pydocstyle
    for w_file in wandb_files:
        select = "--select=D205,D212,D400,D401,D402,D403,D404,D405,D417 "
        print(w_file)
        # os.system(f"pydocstyle {select} {w_file}")
