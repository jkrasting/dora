#!/usr/bin/env python

""" Light-weight XML Parser for FRE XMLs """

import os
import sys

from lxml import etree as ET


def fix_path(path):
    """Formats path-like strings to ensure directories end with a
    trailing slash and double slashes are removed

    Parameters
    ----------
    path : str, path-like
        Path string to reformat

    Returns
    -------
    str
        Reformatted path string
    """
    if len(path) > 0:
        path = path.replace("//", "/")
        path = path + "/" if path[-1] != "/" else path
    return path


def resolve_paths(path, properties, **kwargs):
    """Resolved abstracted properties in path strings

    Parameters
    ----------
    path : lxml.etree._Element
        Path element from XML
    properties : dict
        Dictionary of property key,value pairs

    Returns
    -------
    dict
        Dictionary of resolved paths
    """
    local_properties = {k: v for (k, v) in kwargs.items() if v is not None}
    local_properties = {**properties, **path.attrib, **local_properties}

    paths = {child.tag: child.text for child in path if isinstance(child.tag, str)}
    if "scripts" not in paths.keys():
        paths["scripts"] = "$(rootDir)/$(name)/$(platform)-$(target)/scripts"
    if "analysis" not in paths.keys():
        paths["analysis"] = "$(rootDir)/$(name)/$(platform)-$(target)/scripts"
    if "archive" not in paths.keys():
        paths["archive"] = ""
    if "postProcess" not in paths.keys():
        paths["postProcess"] = ""

    return {
        k: fix_path(sub_properties(v, local_properties)) for (k, v) in paths.items()
    }


def sub_properties(strobj, properties, **kwargs):
    """Substitues XML properties in a string

    Parameters
    ----------
    strobj : str
        String containing unresolved properties
    properties : dict
        Dictionary of key,value properties from XML

    Returns
    -------
    str
        Resolved string
    """
    local_properties = {k: v for (k, v) in kwargs.items() if v is not None}
    local_properties = {**properties, **local_properties}
    count = 1
    while count > 0:
        count = 0
        for (key, value) in local_properties.items():
            if f"${key}" in strobj or f"$({key})" in strobj:
                strobj = strobj.replace(f"$({key})", value)
                strobj = strobj.replace(f"${key}", value)
                count += 1
    return strobj


def parse_xml(xmlfile, user=None):
    """Parses a Flexible Runtime Environment (FRE) XML and returns
    a experiment names, platforms, and path locations

    Parameters
    ----------
    xmlfile : str, path-like
        Path to XML file
    user : str, optional
        Specify a user name, otherwise `logname` is extracted from,
        the environment variable set, by default None

    Returns
    -------
    tuple
        (list of experiment names, list of platforms, dictionary of paths)
    """
    # Light-weight parser for FRE (Flexibile Runtime Environment) Experiments
    tree = ET.parse(xmlfile)
    tree.xinclude()
    root = tree.getroot()

    # resolve xml properties
    properties = {}
    for _property in root.iter("property"):
        properties[_property.attrib["name"]] = _property.attrib["value"]

    # get username
    properties["USER"] = os.environ["LOGNAME"] if user is None else user
    properties["ARCHIVE"] = "/archive/$USER"
    properties["archiveDir"] = "$(archive)"
    properties["rootDir"] = "/home/$(USER)/$(stem)"

    # some gaea-specific properties
    properties["CPERM"] = "/lustre/f1/unswept"
    properties["CDATA"] = "/lustre/f1/pdata"
    properties["CTMP"] = "/lustre/f1"
    properties["DEV"] = "/lustre/f2/dev"

    # set archive property
    # properties["archiveDir"] = "$(_GFDL_ARCHIVE)"
    properties["_GFDL_ARCHIVE"] = f"/archive/{properties['USER']}"
    properties["_GAEA_ARCHIVE"] = f"{properties['CTMP']}/{properties['USER']}"

    # define FRE targets
    targets = ["prod", "repro", "debug"]
    targets = sorted(targets + [f"{x}-openmp" for x in targets])

    # get list of experiments
    exps = [
        sub_properties(x.attrib["name"], properties)
        for x in root
        if x.tag == "experiment"
    ]

    # get list of platforms
    platforms = [
        sub_properties(x.attrib["name"], properties) for x in root.iter("platform")
    ]

    # directories
    directories = {}
    for platform in root.iter("platform"):
        _directories = {
            platform.attrib["name"]: resolve_paths(
                i, properties, platform=platform.attrib["name"]
            )
            for i in platform.iter("directory")
        }
        _directories = {
            k: {i: fix_path(sub_properties(j, v)) for (i, j) in v.items()}
            for (k, v) in _directories.items()
        }
        directories = {**directories, **_directories}

    # iterate of platform/target combos
    resolved_paths = {}
    for target in targets:
        _paths = {
            f"{k}-{target}": {
                i: sub_properties(j, {}, target=target) for (i, j) in v.items()
            }
            for (k, v) in directories.items()
        }
        resolved_paths = {**resolved_paths, **_paths}

    # iterate over experiments
    resolved_paths = {
        x: {
            k: {i: fix_path(sub_properties(j, {}, name=x)) for (i, j) in v.items()}
            for (k, v) in resolved_paths.items()
        }
        for x in exps
    }

    return (exps, platforms, resolved_paths)


if __name__ == "__main__":
    xmlfile_ = sys.argv[1]

    A = parse_xml(xmlfile_)
