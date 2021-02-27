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


def jsonify_dirtree(dirpath):
    """Function to return json of directory tree"""

    filelist = []
    for component in os.scandir(dirpath):
        if component.name.startswith("ocean") and component.is_dir():
            for pptype in os.scandir(component):
                if pptype.name.startswith("av"):
                    for timechunk in os.scandir(pptype):
                        if timechunk.is_dir():
                            for filename in os.scandir(timechunk):
                                filelist.append(
                                    f"{component.name}/{pptype.name}/{timechunk.name}/{filename.name}"
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
    imgbuf.seek(0)
    uri = "data:image/png;base64," + base64.b64encode(imgbuf.getvalue()).decode(
        "utf-8"
    ).replace("\n", "")
    return uri


@app.route("/testmenu")
def browser():
    pathpp = "/Users/krasting/doratest/archive/Raphael.Dussin/FMS2019.01.03_devgfdl_20201120/CM4_piControl_c192_OM4p125_MZtuning/gfdl.ncrc4-intel18-prod-openmp/pp"
    jsondir = jsonify_dirtree(pathpp)
    return render_template("file-browser.html", pathpp=pathpp, jsondir=jsondir)


@app.route("/analysis/om4labs", methods=["GET"])
def om4labs_start():
    idnum = request.args.get("id")
    if idnum is None:
        return render_template("om4labs-splash.html")

    experiment = Experiment(idnum)

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

    files = request.args.get("files")
    if files is None:
        jsondir = jsonify_dirtree(experiment.pathPP)
        return render_template(
            "file-browser.html", jsondir=jsondir, analysis=analysis, idnum=idnum
        )
    if len(files) == 0:
        jsondir = jsonify_dirtree(experiment.pathPP)
        return render_template(
            "file-browser.html", jsondir=jsondir, analysis=analysis, idnum=idnum
        )
    files = files.split(",")
    files = [f"{experiment.pathPP}/{x}" for x in files if not x.startswith("j1")]

    dict_args = om4labs.diags.__dict__[analysis].parse(template=True)
    dict_args["platform"] = "gfdl"
    dict_args["format"] = "stream"
    dict_args["infile"] = files
    # dict_args["obsfile"] = "/Users/krasting/pkgs/om4labs/testing/test_data/obs/WOA13_ptemp+salinity_annual_35levels.nc"
    imgbufs = om4labs.diags.__dict__[analysis].run(dict_args)
    figures = [base64it(x) for x in imgbufs]
    print(files)
    return render_template(
        "om4labs-results.html", figures=figures, experiment=experiment
    )
