from app import app

from flask import render_template
from flask import request
from flask import Response
from flask_login import current_user

from .Experiment import Experiment
import gfdlvitals

import io
import base64

import matplotlib.pyplot as plt

plt.switch_backend("Agg")


def stream_template(template_name, **context):
    # if not current_user.is_authenticated:
    #    ## possibly needed, broke with login:
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv


@app.route("/analysis/scalar")
def scalardiags():

    idnum = request.args.getlist("id")
    idnum = [] if len(idnum) == 0 else idnum

    if len(idnum) == 0:
        return render_template("scalar-splash.html")

    region = request.args.get("region")
    realm = request.args.get("realm")
    smooth = request.args.get("smooth")
    nyears = request.args.get("nyears")
    trend = request.args.get("trend")
    align = request.args.get("align")

    trend = True if trend is not None else False
    align = True if align is not None else False

    smooth = None if (smooth == "" or smooth is None) else int(smooth)
    nyears = None if (nyears == "" or nyears is None) else int(nyears)

    if (region is None) or (realm is None):
        return render_template("scalar-menu.html", id=idnum)

    exper = {x: Experiment(x) for x in idnum}

    # validate experiments before continuing
    validated = {k: v.validate_path("pathDB") for k, v in exper.items()}
    failed = [x for x in list(exper.keys()) if validated[x] is False]
    exper = [exper[x] for x in list(exper.keys()) if validated[x] is True]
    if len(failed) > 0:
        return render_template(
            "page-500.html", msg=f"Unable to locate {str(',').join(failed)}"
        )

    dset = [f"{x.pathDB}/{region}Ave{realm}.db" for x in exper]
    dset = [gfdlvitals.open_db(x) for x in dset]
    labels = [x.expName for x in exper]
    labels = str(",").join(labels)

    def plot_gen():
        for x in sorted(list(dset[0].columns)):
            fig = gfdlvitals.plot_timeseries(
                dset,
                trend=trend,
                smooth=smooth,
                var=x,
                nyears=nyears,
                align_times=align,
                labels=labels,
            )
            fig = fig[0]
            imgbuf = io.BytesIO()
            fig.savefig(imgbuf, format="png", bbox_inches="tight", dpi=72)
            plt.close(fig)
            imgbuf.seek(0)
            uri = "data:image/png;base64," + base64.b64encode(imgbuf.getvalue()).decode(
                "utf-8"
            ).replace("\n", "")
            yield uri

    content = {
        "rows": plot_gen(),
        "region": region.capitalize(),
        "realm": realm.capitalize(),
    }
    return Response(stream_template("scalar-diags.html", **content))
