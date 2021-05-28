from app.project_util import list_projects
import base64
import glob
import io
from operator import itemgetter
from operator import attrgetter
import os
import traceback

import om4labs
from flask import render_template
from flask import request
from flask import send_file

from app import app
from .Experiment import Experiment

from .frepptools import list_components, Componentgroup, compare_compgroups


@app.route("/analysis/diffmaps", methods=["GET"])
def diffmaps_start():
    """Flask route model-model comparison maps

    Returns
    -------
    Jinja template name and variables for rendering
    """

    # Get the experiment ID number from the URL or provide user with
    # a form to enter a post-processing path directly
    idnum = request.args.getlist("id")
    if len(idnum) != 2:
        return render_template("diffmaps-splash.html")

    # Get an Experiment object for each idnumber
    experiments = [Experiment(x) for x in idnum]

    # Get the requested component and send user to the file selector
    # if it is not defined
    component = request.args.get("component")
    if component is None:
        # list components
        ppdirs = [x.pathPP for x in experiments]
        components = [set(list_components(x)) for x in ppdirs]
        components = list(components[0].intersection(components[1]))
        components = sorted(components)
        # filter out passage flow components
        components = [x for x in components if not x.split("_")[1][0].isupper()]
        return render_template(
            "diffmaps-selector.html",
            component=component,
            components=components,
            idnum=idnum,
            infiles=None,
            file1=None,
            file2=None,
        )

    # Determine if overlapping files is requested
    common = True if request.args.get("common") is not None else False

    # create a component group object for each experiment and resolve the files
    groups = [Componentgroup(x.pathPP, component, experiment=x) for x in experiments]
    groups = [x.resolve_files() for x in groups]

    # if common times are requested, find overlap between two experiments
    if common:
        compare_compgroups(groups[0], groups[1])

    # get list of files from the command line
    file1 = request.args.getlist("file1")
    file2 = request.args.getlist("file2")

    # if no files are selected, send user to the file seclector
    if len(file1) == 0:
        return render_template(
            "diffmaps-selector.html",
            component=component,
            common=common,
            groups=groups,
            idnum=idnum,
            infiles=None,
            file1=None,
            file2=None,
        )

    # if common times requested, use the same filelist for both
    if common:
        file2 = file1

    # weed out files that are not requested
    groups[0] = groups[0].exclude_files(file1)
    groups[1] = groups[1].exclude_files(file2)

    # resolve paths
    infiles = [x.reconstitute_files() for x in groups]
    infiles = [x for sublist in infiles for x in sublist]

    # See if the user acknowleged the need to pre-dmget the files
    validated = request.args.get("validated")

    # If the user has *not* validated the files, display a list
    # of files that the user should dmget on their own
    if validated is None:
        return render_template(
            "diffmaps-selector.html",
            component=component,
            common=common,
            groups=groups,
            idnum=idnum,
            file1=file1,
            file2=file2,
            infiles=infiles,
        )

    return ""
