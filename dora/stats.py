from dora import dora

from flask import render_template
from flask import request
from flask import Response
from flask_login import current_user

from .Experiment import Experiment
import gfdlvitals

import io
import base64

import matplotlib.pyplot as plt
import pandas as pd

plt.switch_backend("Agg")


def stream_template(template_name, **context):
    # if not current_user.is_authenticated:
    #    ## possibly needed, broke with login:
    dora.update_template_context(context)
    t = dora.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv


@dora.route("/analysis/stats")
def stats():

    # Fetch experiments
    idnum = request.args.getlist("id")
    idnum = [] if len(idnum) == 0 else idnum

    if len(idnum) == 0:
        return render_template("stats-splash.html")

    # Sanity check
    if (len(idnum) != 2) or (any(x == "" for x in idnum)):
        return render_template(
            "page-500.html", msg="You must specify exactly 2 experiments."
        )

    # Determine which region and component to analyze
    region = request.args.get("region")
    realm = request.args.get("realm")

    # Get additional options
    nyears = request.args.get("nyears")
    nyears = None if (nyears == "" or nyears is None) else int(nyears)
    pval = request.args.get("pval")
    pval = 0.05 if (pval == "" or pval is None) else float(pval)

    # Prompt user if essentials are missing
    if (region is None) or (realm is None):
        return render_template("stats-menu.html", id=idnum)

    # Fetch VitalsDataFrame objects
    exper = [Experiment(x) for x in idnum]
    dset = [f"{x.pathDB}/{region}Ave{realm}.db" for x in exper]
    dset = [gfdlvitals.open_db(x) for x in dset]

    # Limit length if requested
    if nyears is not None:
        dset = [x[0 : int(nyears)] for x in dset]

    # Set number formatting options
    pd.set_option("display.float_format", lambda x: "%.7f" % x)

    # Run the t-test
    pvals = dset[0].ttest(dset[1])
    pvals = pvals.loc[pvals["pval"] <= pval]

    # Calculate mean values
    df0 = dset[0].mean(axis=0).to_frame(name=f"1. {exper[0].expName}")
    df1 = dset[1].mean(axis=0).to_frame(name=f"2. {exper[1].expName}")

    # Merge the DataFrames
    result = pd.concat([df0, df1, pvals], axis=1, join="inner")
    result = result.to_html()

    return render_template("stats-results.html", pval=pval, result=result)
