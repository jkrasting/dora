import os
import json

from app import app

from flask import render_template
from flask import request
from flask import Response
from flask_login import current_user

from .Experiment import Experiment
import io
import base64
import om4labs


def jsonify_dirtree(dirpath, pptype="av"):
    """Returns a post-processing directory tree

    Parameters
    ----------
    dirpath : str, path-like
        Path to top-level "pp" directory
    pptype : str, optional
        Type of post-processed files to return
        either "av" or "ts", by default "av"

    Returns
    -------
    dict
        Dictionary of files and options to pass to file browser
    """

    filelist = []
    if pptype == "av":
        for component in os.scandir(dirpath):
            if (
                component.name.startswith("ocean") or component.name.startswith("ice")
            ) and component.is_dir():
                for pptype in os.scandir(component):
                    if pptype.name.startswith("av"):
                        for timechunk in os.scandir(pptype):
                            if timechunk.is_dir():
                                for filename in os.scandir(timechunk):
                                    filelist.append(
                                        f"{component.name}/{pptype.name}/{timechunk.name}/{filename.name}"
                                    )

    elif pptype == "ts":
        for component in os.scandir(dirpath):
            print(component)
            if (
                component.name.startswith("ocean") or component.name.startswith("ice")
            ) and component.is_dir():
                for pptype in os.scandir(component):
                    if pptype.name.startswith("ts"):
                        for freq in os.scandir(pptype):
                            if freq.is_dir():
                                for timechunk in os.scandir(freq):
                                    if timechunk.is_dir():
                                        for filename in os.scandir(timechunk):
                                            filelist.append(
                                                f"{component.name}/{pptype.name}/{freq.name}/{timechunk.name}/{filename.name}"
                                            )

    filelist = sorted(filelist)
    filesplit = sorted([x.split("/") for x in filelist])
    dirs = sorted(list(set([str("/").join(x[0:3]) for x in filesplit])))

    filedict = {
        "id": "",
        "text": "pp",
        "icon": "jstree-folder",
        "state": {"opened": "true"},
        "children": [
            {
                "id": "",
                "text": directory,
                "icon": "jstree-folder",
                "children": [
                    {
                        "id": x,
                        "text": x.replace(f"{directory}/", ""),
                        "icon": "jstree-file",
                    }
                    for x in filelist
                    if x.startswith(directory)
                ],
            }
            for directory in dirs
        ],
    }
    return filedict


def base64it(imgbuf):
    """Converts in-memory PNG image to inlined ASCII format

    Parameters
    ----------
    imgbuf : io.BytesIO
        Binary memory buffer cotaining PNG image

    Returns
    -------
    str
        Base64 representation of the image
    """
    imgbuf.seek(0)
    uri = "data:image/png;base64," + base64.b64encode(imgbuf.getvalue()).decode(
        "utf-8"
    ).replace("\n", "")
    return uri


@app.route("/analysis/om4labs", methods=["GET"])
def om4labs_start():
    """Flask route for calling OM4Labs

    Returns
    -------
    Jinja template name and variables for rendering
    """

    # Get the experiment ID number from the URL or provide user with
    # a form to enter a post-processing path directly
    idnum = request.args.get("id")
    if idnum is None:
        return render_template("om4labs-splash.html")

    # Fetch an Experiment object that houses all of the
    # experiment metadata
    experiment = Experiment(idnum)

    # Get the requested analysis from the URL or provide user with
    # a menu of available diagnostics in OM4Labs
    analysis = request.args.get("analysis")
    if analysis is None:
        avail_diags = [x for x in dir(om4labs.diags) if not x.startswith("__")]
        exclude = ["avail", "generic"]
        avail_diags = [x for x in avail_diags if not any(diag in x for diag in exclude)]
        avail_diags = [
            (diag, eval(f"om4labs.diags.{diag}.__description__"))
            for diag in avail_diags
        ]
        print(avail_diags)
        return render_template(
            "om4labs-start.html", avail_diags=avail_diags, idnum=idnum
        )

    # Get the list of files to analyse from the URL or provide user with
    # a clickable menu to browse for files to analyse
    files = request.args.get("files")

    # The "section transports" diagnostic accepts a top-level pp dir
    if analysis in ["section_transports"]:
        files = []
    else:
        pptype = "ts" if analysis == "seaice" else "av"
        files = "" if files is None else files
        if len(files) == 0:
            jsondir = jsonify_dirtree(experiment.pathPP, pptype=pptype)
            return render_template(
                "file-browser.html", jsondir=jsondir, analysis=analysis, idnum=idnum
            )
        files = files.split(",")

    # infer static file from frepp structure
    if len(files) > 0:
        static = files[0].split("/")[0]
        static = f"{experiment.pathPP}/{static}/{static}.static.nc"
        files = [f"{experiment.pathPP}/{x}" for x in files if not x.startswith("j1")]
    else:
        static = None

    # Intialize and empty dictionary of options pertaining to the
    # requested diagnostic
    dict_args = om4labs.diags.__dict__[analysis].parse(template=True)

    # Tell OM4Labs we want streaming image buffers back
    dict_args["format"] = "stream"

    # Populate various options for running the diagnostic from
    # the experiment metadata
    dict_args["label"] = experiment.expName
    dict_args["ppdir"] = [experiment.pathPP]

    dict_args["dataset"] = "NSIDC_NH_monthly"

    # Tell OM4Labs where to find the observational data
    dict_args["platform"] = os.environ["OM4LABS_PLATFORM"]

    # Pass in the paths to the selected files and the inferred
    # static / topog file
    dict_args["infile"] = files
    dict_args["static"] = static
    dict_args["topog"] = static

    # *** Run OM4Labs ***
    imgbufs = om4labs.diags.__dict__[analysis].run(dict_args)

    # Convert image buffers to in-lined images
    figures = [base64it(x) for x in imgbufs]

    return render_template(
        "om4labs-results.html", figures=figures, experiment=experiment
    )
