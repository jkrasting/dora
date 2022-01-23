import os

from app import app
from .db import get_db
from .xml import parse_xml
from flask import request
from flask import render_template
from .projects import create_project_map
from .projects import associate_with_project

from .Experiment import Experiment


@app.route("/experiment/<experiment_id>")
def view_experiment(experiment_id):
    exper = Experiment(experiment_id)
    return render_template(
        "experiment_view.html", experiment=exper, experiment_id=experiment_id
    )


@app.route("/admin/experiment/<experiment_id>", methods=["GET", "POST"])
def expadmin(experiment_id=None):
    if experiment_id == "new":
        args = dict(request.form)
        if "xmlfile" not in list(args.keys()):
            return render_template("experiment-add-splash.html")
        else:
            if os.path.exists(args["xmlfile"]):
                if os.path.isdir(args["xmlfile"]):
                    expobj = Experiment(args["xmlfile"])
                    expobj.id = "new"
                    print(expobj)
                    return render_template("experiment-review.html", expobj=expobj)

            exps, platforms, paths = parse_xml(args["xmlfile"], user=args["user"])
            exps = sorted(exps)
            platforms = sorted([x for x in platforms if "gfdl" not in x])
            targets = ["prod", "repro", "debug"]
            targets = sorted(targets + [f"{x}-openmp" for x in targets])
            if not all(
                item in list(args.keys())
                for item in ["experiment", "platform", "target", "user"]
            ):
                return render_template(
                    "experiment-add-options.html",
                    xmlfile=args["xmlfile"],
                    exps=exps,
                    targets=targets,
                    platforms=platforms,
                    user=args["user"],
                )
            else:
                platform_target = f"{args['platform']}-{args['target']}"
                gfdlplatform = "gfdl." + platform_target.replace(".", "-")
                directories = paths[args["experiment"]][platform_target]
                gfdldirectories = paths[args["experiment"]][gfdlplatform]
                expdict = {}
                expdict["id"] = "new"
                expdict["userName"] = args["user"]
                expdict["pathXML"] = args["xmlfile"]
                expdict["pathScript"] = directories["scripts"] + args["experiment"]
                expdict["expName"] = args["experiment"]
                expdict["pathPP"] = gfdldirectories["postProcess"]
                expdict["pathAnalysis"] = gfdldirectories["analysis"]
                expdict["pathDB"] = gfdldirectories["scripts"].replace(
                    "/scripts", "/db"
                )
                expobj = Experiment(expdict)
                _ = [
                    expobj.remove_key(x)
                    for x in expobj.list_keys()
                    if expobj.value(x) is None
                ]
                return render_template("experiment-review.html", expobj=expobj)
    else:
        expobj = Experiment(experiment_id)
        return render_template("experiment-review.html", expobj=expobj)


@app.route("/admin/experiment_update.html", methods=["POST"])
def experiment_update():
    args = dict(request.form)
    projs = request.form.getlist("projects")
    exper = Experiment(args)
    db = get_db()
    if exper.id == "new":
        _id = exper.insert(db)
        for project in projs:
            create_project_map(project)
            associate_with_project(_id, project)
        return render_template(
            "success.html", msg=f"New experiment added as ID#: {_id}"
        )
    else:
        exper.update(db)
        return render_template("success.html", msg=f"Updated experiment {exper.id}")
