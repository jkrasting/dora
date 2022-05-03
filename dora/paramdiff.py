from dora import dora

from flask import render_template
from flask import request
from flask import Response
from flask_login import current_user

from .Experiment import Experiment
import mom6_parameter_scanner


class NullResult:
    def __init__(self):
        self.dict = {}


def parameter_diff(params):

    # get a list of dicts of parameter differences
    diffs = [set(list(x.dict.items())) for x in params]
    intersection = set.intersection(*diffs)
    diffs = [dict(x - intersection) for x in diffs]

    # list of keys that differ across the set of experiments
    diff_keys = set([k for x in diffs for k in list(x.keys())])
    diff_keys = sorted(list(diff_keys))

    # function to set missing values to double-dash
    fill_out = lambda param, diff_keys: [
        param[k] if k in list(param.keys()) else "--" for k in diff_keys
    ]

    # list of tuples of differing values
    diff_vals = [(fill_out(x, diff_keys)) for x in diffs]
    diff_vals.insert(0, diff_keys)
    diff_vals = list(zip(*diff_vals))

    return diff_vals


@dora.route("/analysis/parameters")
def paramscan():

    idnum = request.args.getlist("id")

    if len(idnum) == 1:
        idnum = idnum[0]
        idnum = [] if idnum == "" else idnum.replace(" ", "").split(",")

    if len(idnum) == 0:
        return render_template("parameter-splash.html")

    exper = [Experiment(x) for x in idnum]
    names = [x.expName for x in exper]
    dirs = [x.pathPP.replace("/pp", "/ascii") for x in exper]

    header = list(zip(idnum, names))

    # MOM Log File
    mom_msg = []
    try:
        mom = [mom6_parameter_scanner.Parameters(x) for x in dirs]
    except Exception as e:
        mom = [NullResult()]
        mom_msg.append(str(e))
    mom = parameter_diff(mom)

    # SIS Log File
    sis_msg = []
    try:
        sis = [
            mom6_parameter_scanner.Parameters(
                x,
                parameter_files=["*SIS_parameter_doc.all", "*SIS_parameter_doc.short"],
            )
            for x in dirs
        ]
    except Exception as e:
        sis = [NullResult()]
        sis_msg.append(str(e))
    sis = parameter_diff(sis)

    # FMS Log File 0
    log0_msg = []
    try:
        log0 = [
            mom6_parameter_scanner.Log(x, parameter_files=["*logfile.000000.out"])
            for x in dirs
        ]
    except Exception as e:
        log0 = [NullResult()]
        log0_msg.append(str(e))
    log0 = parameter_diff(log0)

    # FMS Log File 1
    log1_msg = []
    try:
        log1 = [
            mom6_parameter_scanner.Log(x, ignore_files=["*logfile.000000.out"])
            for x in dirs
        ]
    except Exception as e:
        log1 = [NullResult()]
        log1_msg.append(str(e))
    log1 = parameter_diff(log1)

    # FMS Namelist 0
    namelist0_msg = []
    try:
        namelist0 = [
            mom6_parameter_scanner.Namelists(x, parameter_files=["*logfile.000000.out"])
            for x in dirs
        ]
    except Exception as e:
        namelist0 = [NullResult()]
        namelist0_msg.append(str(e))
    namelist0 = parameter_diff(namelist0)

    # FMS Namelist 1
    namelist1_msg = []
    try:
        namelist1 = [
            mom6_parameter_scanner.Namelists(x, ignore_files=["*logfile.000000.out"])
            for x in dirs
        ]
    except Exception as e:
        namelist1 = [NullResult()]
        namelist1_msg.append(str(e))
    namelist1 = parameter_diff(namelist1)

    return render_template(
        "parameter-diff.html",
        header=header,
        mom=mom,
        sis=sis,
        log0=log0,
        log1=log1,
        namelist0=namelist0,
        namelist1=namelist1,
        mom_msg=mom_msg,
        sis_msg=sis_msg,
        log0_msg=log0_msg,
        log1_msg=log1_msg,
        namelist0_msg=namelist0_msg,
        namelist1_msg=namelist1_msg,
    )
