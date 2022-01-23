from app import app

from flask import render_template
from flask import request
from flask import Response
from flask_login import current_user

from .Experiment import Experiment
from .db import get_db
import gfdlvitals

import io

@app.route("/api/info")
def exp_info():
    idnum = request.args.get("id")
    return Experiment(idnum).to_dict()

@app.route("/api/data")
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


@app.route("/api/search")
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

    return {x["id"]:x for x in result}