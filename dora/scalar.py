from dora import dora

from flask import render_template
from flask import request
from flask import Response
from flask_login import current_user

from .Experiment import Experiment
import gfdlvitals

import io
import base64
import os

import matplotlib.pyplot as plt

plt.switch_backend("Agg")


def stream_template(template_name, **context):
    # if not current_user.is_authenticated:
    #    ## possibly needed, broke with login:
    dora.update_template_context(context)
    t = dora.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv


def gfdlvitals_plot(
    dset,
    x,
    labels=None,
    trend=None,
    align=None,
    smooth=None,
    nyears=None,
    plottype="average",
    raise_exception=True,
    title="both",
):
    try:
        fig = gfdlvitals.plot_timeseries(
            dset,
            trend=trend,
            smooth=smooth,
            var=x,
            nyears=nyears,
            align_times=align,
            plottype=plottype,
            labels=labels,
            title=title,
        )
        fig = fig[0]
        imgbuf = io.BytesIO()
        fig.savefig(imgbuf, format="png", bbox_inches="tight", dpi=72)
        plt.close(fig)
        imgbuf.seek(0)
        uri = "data:image/png;base64," + base64.b64encode(imgbuf.getvalue()).decode(
            "utf-8"
        ).replace("\n", "")
        uri = '<img src="' + uri + '">'
    except Exception as e:
        uri = "Caught Exception: " + str(e)
        if raise_exception:
            raise e
    return uri


def format_label(x):
    """Formats the experiment label"""
    label = f"{x.requested_id} - " if x.source == "sql" else ""
    label = label + x.expName
    return label


@dora.route("/analysis/scalar")
def scalardiags():
    idnum = request.args.getlist("id")

    if len(idnum) == 1:
        idnum = idnum[0]
        idnum = [] if idnum == "" else idnum.replace(" ", "").split(",")

    if len(idnum) == 0:
        return render_template("scalar-splash.html")

    region = request.args.get("region")
    realm = request.args.get("realm")
    smooth = request.args.get("smooth")
    nyears = request.args.get("nyears")
    trend = request.args.get("trend")
    align = request.args.get("align")
    plottype = request.args.get("plottype")

    trend = True if trend is not None else False
    align = True if align is not None else False
    plottype = "average" if plottype is None else plottype

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

    def obgc_hack(in_path):
        if "OBGC" in realm:
            if not os.path.exists(in_path):
                if not os.path.exists(in_path.replace("OBGC.db", "COBALT.db")):
                    if not os.path.exists(in_path.replace("OBGC.db", "BLING.db")):
                        raise FileNotFoundError(
                            "Unable to locate appropriate OBGC, COBALT, or BLING .db file"
                        )
                    else:
                        return in_path.replace("OBGC.db", "BLING.db")
                else:
                    return in_path.replace("OBGC.db", "COBALT.db")
            else:
                return in_path
        else:
            return in_path

    dbfilename = f"{region}Ave{realm}.db"
    filepaths = [
        (idx, x.pathDB, obgc_hack(f"{x.pathDB}{dbfilename}").replace(x.pathDB, ""))
        for idx, x in zip(idnum, exper)
    ]
    dset = [gfdlvitals.open_db(f"{x[1]}{x[2]}") for x in filepaths]
    dset = [x.build_netrad_toa() for x in dset]
    labels = [format_label(x) for x in exper]
    labels = str(",").join(labels)

    def plot_gen():
        for x in sorted(list(dset[0].columns)):
            uri = gfdlvitals_plot(
                dset,
                x,
                raise_exception=False,
                labels=labels,
                trend=trend,
                align=align,
                smooth=smooth,
                nyears=nyears,
                plottype=plottype,
                title="longname",
            )
            yield (x, uri)

    content = {
        "rows": plot_gen(),
        "region": region.capitalize(),
        "realm": realm.capitalize(),
        "filepaths": filepaths,
    }
    return Response(stream_template("scalar-diags.html", **content))
