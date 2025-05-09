from __future__ import annotations

from typing import Any, Iterable


def process_subconfigs(config, subconfig_names: Iterable[str]) -> list[dict[str, Any]]:
    """Applies some processing logic to config entries."""
    subconfigs = []
    for name in subconfig_names:
        subconfig = dict(config[name])

        # If add-elements is empty, keep the list empty instead of setting it to `[""]`
        add_elements = subconfig["add-elements"].split(",")
        subconfig["add-elements"] = [s for s in map(str.strip, add_elements) if s]

        # If elements is empty, keep the list empty instead of setting it to `[""]`
        elements = subconfig["elements"].split(",")
        subconfig["elements"] = [s for s in map(str.strip, elements) if s]

        subconfigs.append(subconfig)
    return subconfigs
