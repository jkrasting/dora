#!/usr/bin/env python

import hashlib
import fnmatch
import os, sys
#import webtoolbox, cgitb
from lxml import etree as ET

from icecream import ic

def fix_path(x):
    if len(x) > 0:
        x = x.replace("//","/")
        x = x+"/" if x[-1] != "/" else x
    return x

def resolve_paths(x,properties,**kwargs):
    local_properties = {k:v for (k,v) in kwargs.items() if v is not None}
    local_properties = {**properties,**x.attrib,**local_properties}

    paths = {child.tag:child.text for child in x if isinstance(child.tag,str)}
    if "scripts" not in paths.keys():
        paths["scripts"] = "$(rootDir)/$(name)/$(platform)-$(target)/scripts"
    if "analysis" not in paths.keys():
        paths["analysis"] = "$(rootDir)/$(name)/$(platform)-$(target)/scripts"
    if "archive" not in paths.keys():
        paths["archive"] = ""
    if "postProcess" not in paths.keys():
        paths["postProcess"] = ""

    return {k:fix_path(sub_properties(v,local_properties)) for (k,v) in paths.items()}

def sub_properties(x,properties,**kwargs):
    local_properties = {k:v for (k,v) in kwargs.items() if v is not None}
    local_properties = {**properties,**local_properties}
    count = 1
    while count > 0:
        count = 0
        for (k,v) in local_properties.items():
            if f"${k}" in x or f"$({k})" in x:
                x = x.replace(f"$({k})",v)
                x = x.replace(f"${k}",v)
                count += 1
    return x

def frelist(
    xmlfile,
    result="experiments",
    experiment="",
    platform="",
    target="",
    user=None,
    gfdl=False,
):
    """Light-weight parser for FRE (Flexibile Runtime Environment) Experiments

    Parameters
    ----------
    xmlfile : str, path-like
        [description], by default None
    result : str, optional
        [description], by default "experiments"
    experiment : str, optional
        [description], by default ""
    platform : str, optional
        [description], by default ""
    target : str, optional
        [description], by default ""
    user : str, optional
        [description], by default ""
    gfdl : bool, optional
        [description], by default False

    Returns
    -------
    [type]
        [description]
    """
    if gfdl is True:
        platform = "gfdl." + "-".join(platform.split("."))
    _result = []
    tree = ET.parse(xmlfile.replace("/home/", "/gfdlhome/"))
    tree.xinclude()
    ic(tree)
    root = tree.getroot()
    ic(root)

    # resolve xml properties
    properties = {}
    for _property in root.iter("property"):
        properties[_property.attrib["name"]] = _property.attrib["value"]

    # get username
    properties["USER"] = os.environ['LOGNAME'] if user is None else user
    properties["ARCHIVE"] = "/archive/$USER"
    properties["archiveDir"] = "$(archive)"
    properties["rootDir"] = "/home/$(USER)/$(stem)"

    # some gaea-specific properties
    properties["CPERM"] = "/lustre/f1/unswept"
    properties["CDATA"] = "/lustre/f1/pdata"
    properties["CTMP"] = "/lustre/f1"
    properties["DEV"] = "/lustre/f2/dev"

    # set archive property
    #properties["archiveDir"] = "$(_GFDL_ARCHIVE)"
    properties["_GFDL_ARCHIVE"] = f"/archive/{properties['USER']}"
    properties["_GAEA_ARCHIVE"] = f"{properties['CTMP']}/{properties['USER']}"

    # define FRE targets
    targets = ["prod","repro","debug"]

    # get list of experiments
    exps = [sub_properties(x.attrib["name"],properties) for x in root if x.tag == "experiment"]
    ic(exps)

    # get list of platforms
    platforms = [sub_properties(x.attrib["name"],properties) for x in root.iter("platform")]
    ic(platforms)

    # directories
    directories = {}
    for x in root.iter("platform"):
        _directories = {x.attrib["name"]:resolve_paths(i,properties,platform=x.attrib["name"]) for i in x.iter("directory")}
        _directories = {k:{i:fix_path(sub_properties(j,v)) for (i,j) in v.items()} for (k,v) in _directories.items()}
        directories = {**directories,**_directories}

    paths = {}
    for target in targets:
        _paths = {f"{k}-{target}":{i:sub_properties(j,{},target=target) for (i,j) in v.items()} for (k,v) in directories.items()}

if __name__ == "__main__":
    xmlfile = sys.argv[1]

    frelist(xmlfile)
