def process_subconfigs(config, subconfig_names):
    """Applies some processing logic to config entries."""
    subconfigs = []
    for name in subconfig_names:
        subconfig = dict(config[name])
        subconfig["add-elements"] = subconfig["add-elements"].split(",")
        subconfig["elements"] = subconfig["elements"].split(",")
        subconfigs.append(subconfig)
    return subconfigs
