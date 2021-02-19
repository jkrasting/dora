from app import app

from flask import render_template
from flask import request
from flask import Response
from flask_login import current_user

from .Experiment import Experiment
import mom6_parameter_scanner


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


@app.route("/paramscan")
def paramscan():

    dir1 = "/Users/krasting/doratest/archive/Raphael.Dussin/FMS2019.01.03_devgfdl_20201120/CM4_piControl_c96_OM4p25_kdadd/gfdl.ncrc4-intel18-prod-openmp/ascii"
    dir2 = "/Users/krasting/doratest/archive/Raphael.Dussin/FMS2019.01.03_devgfdl_20201120/CM4_piControl_c192_OM4p125_MZtuning/gfdl.ncrc4-intel18-prod-openmp/ascii"

    dirs = [dir1, dir2]

    mom = [mom6_parameter_scanner.Parameters(x) for x in dirs]
    sis = [
        mom6_parameter_scanner.Parameters(
            x, parameter_files=["*SIS_parameter_doc.all", "*SIS_parameter_doc.short"]
        )
        for x in dirs
    ]

    diffs = parameter_diff(sis)

    print(diffs)

    return ""
