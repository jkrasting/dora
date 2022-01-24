from flask.globals import request
from dora import dora

import hashlib

from flask import render_template
from flask import Response
import mom6_parameter_scanner

from .Experiment import Experiment
from .db import get_db


def capture(func, *args, **kwargs):
    result = {}
    try:
        result = func(*args, **kwargs)
        result = dict(result.dict)
    except:
        pass
    return result


def shrink_substring(X, sub="%,"):
    X = X.split(sub)
    count = 0
    Y = ""
    for x in X:
        if x == "":
            count += 1
        else:
            if count == 0:
                Y = Y + x
            elif count == 1:
                Y = Y + sub + x
            else:
                Y = Y + "[" + str(count) + "*" + sub + "]" + x
                count = 0
    return Y


def stream_template(template_name, **context):
    # if not current_user.is_authenticated:
    #    ## possibly needed, broke with login:
    dora.update_template_context(context)
    t = dora.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv


@dora.route("/param/update/<idnum>")
def update_param_database(idnum):

    exp = Experiment(idnum)

    ID = exp.id
    path_ascii = exp.pathPP.replace("/pp", "/ascii")

    params = {
        **capture(
            mom6_parameter_scanner.Namelists,
            path_ascii,
            ignore_files=["*.logfile.000000.out"],
        ),
        **capture(
            mom6_parameter_scanner.Namelists,
            path_ascii,
            parameter_files=["*.logfile.000000.out"],
        ),
        **capture(
            mom6_parameter_scanner.Parameters,
            path_ascii,
            parameter_files=["*SIS_parameter_doc.all", "*SIS_parameter_doc.short"],
            model_name="SIS2",
        ),
        **capture(mom6_parameter_scanner.Parameters, path_ascii, model_name="MOM6"),
    }

    params = {k: shrink_substring(v) for k, v in params.items()}
    params = {k: v.replace('"', "") for k, v in params.items()}

    print("Inserting values into database")

    db = get_db()
    errors = []
    cursor = db.cursor()
    count = 0
    for k, v in params.items():
        hexkey = hashlib.md5(str(str(ID) + k).encode("utf-8")).hexdigest()
        cmd = (
            f'INSERT INTO parameters set hexkey="{hexkey}", expID="{ID}", '
            + f'param="{k}", val="{v}" ON DUPLICATE KEY UPDATE '
            + f'expID="{ID}", param="{k}", val="{v}";'
        )
        try:
            cursor.execute(cmd)
            db.commit()
            count += 1
        except Exception as e:
            errors.append(f"Error occurred at: {hexkey}, {k}, {v}, {e}")
            pass
    cursor.close()

    return render_template("parameter-update.html", exp=exp, count=count, errors=errors)
