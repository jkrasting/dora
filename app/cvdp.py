import os

from flask import redirect
from flask import render_template
from flask import send_from_directory

from .Experiment import Experiment

from app import app


@app.route("/cvdp/<project_id>")
def view_cvdp_root(project_id):
    # path = "/cvdp_path"
    return redirect(f"/cvdp/{project_id}/index.html", 302)


@app.route("/cvdp/<project_id>/<path:filename>")
def view_cvdp(project_id, filename):
    exper = Experiment(project_id)
    path = f"{exper.pathAnalysis}/cvdp/"
    path = path.replace("//", "/")
    print(path)
    if not os.path.exists(path + filename):
        return render_template("page-404.html"), 404
    else:
        return send_from_directory(path, filename)
