from dora import dora

from flask import render_template
from flask import request
from flask import Response
from flask_login import current_user

from .Experiment import Experiment
from .db import get_db
from .projects import fetch_project_info
from .user import Token, User

import datetime

import gfdlvitals

import io


@dora.route("/api/add")
def add():
    token = request.args.get("token")

    if token is None:
        return "API Token required for this operation."

    token = Token(token)
    
    try:
        assert token.is_valid, "Specified token is not valid. See administrator."
    except AssertionError as exc:
        return str(exc)

    # if not hasattr(token, "token"):
    #     return "Invalid token specified."

    # if token.active == 0:
    #     return "Specified token is not active."

    # if datetime.datetime.now() > token.expires:
    #     return "Token is expired."

    # get parameters from url request
    args = dict(request.args)

    args = {k:args[k] for k in Experiment({}).expected_keys if k in args.keys()}
    args["owner"] = token.user.firstlast

    exp = Experiment(args)
    
    try:
        result = str(exp.insert(None))
    except Exception as exc:    
        result = "Error: " + str(exc)

    return result


@dora.route("/api/info")
def exp_info():
    idnum = request.args.get("id")
    return Experiment(idnum).to_dict()


@dora.route("/api/data")
def csv_data():
    idnum = request.args.get("id")
    component = request.args.get("component")
    experiment = Experiment(idnum)
    if "pathDB" not in list(experiment.to_dict().keys()):
        return ""
    else:
        dbfile = f"{experiment.pathDB}/{component}.db"
        try:
            return gfdlvitals.open_db(dbfile).to_json()
        except:
            return {}


@dora.route("/api/list")
def project_json():
    project_name = request.args.get("project_name")

    result = fetch_project_info(project_name, auth=False)

    if isinstance(result, tuple):
        tables, project_description, parameter, params, error = result
        return {"project": tables}
    else:
        return render_template("page-500.html", msg=result)


@dora.route("/api/search")
def dbsearch():
    search = request.args.get("search")
    sql = (
        "SELECT *  FROM `mdt_tracker`.`master` WHERE (CONVERT(`id` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`owner` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`userName` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`modelType` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`displayName` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`expName` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`expLength` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`expYear` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`expType` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`expMIP` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`expLabels` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`urlCurator` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`pathPP` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`pathAnalysis` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`pathDB` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`pathScript` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`pathXML` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`pathLog` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`status` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`jobID` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`queue` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`gfdlHistoryYear` USING utf8) REGEXP '"
        + search
        + "' OR CONVERT(`refresh` USING utf8) REGEXP '"
        + search
        + "')"
    )

    # open a database connection and cursor
    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()

    return {x["id"]: x for x in result}
