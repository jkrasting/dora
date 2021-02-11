import os
import json

from app import app

from flask import render_template
from flask import request
from flask import Response
from flask_login import current_user

import io
import base64

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
        "state": {"opened": "true"},
        "children": [
            {
                "id": "",
                "text": directory,
                "children": [
                    {"id": x, "text": x.replace(f"{directory}/","")} for x in filelist if x.startswith(directory)
                ],
            }
            for directory in dirs
        ],
    }
    return filedict

@app.route("/testmenu")
def browser():
    pathpp = "/Users/krasting/doratest/archive/Raphael.Dussin/FMS2019.01.03_devgfdl_20201120/CM4_piControl_c192_OM4p125_MZtuning/gfdl.ncrc4-intel18-prod-openmp/pp"
    jsondir = jsonify_dirtree(pathpp)
    return render_template("file-browser.html",pathpp=pathpp,jsondir=jsondir)