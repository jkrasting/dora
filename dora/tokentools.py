import secrets
import datetime

from .db import get_db
from .user import User
from .user import user_experiment_count
from .project_util import *
from .user import check_sql_table_exists, get_api_token

from flask import g

from dora import dora
from flask import request
from flask import render_template
from flask import session
from flask import redirect

from flask_login import current_user, login_required


@dora.route("/admin/tokens")
def list_tokens():
    db = get_db()
    cursor = db.cursor()

    sql = "select * from tokens"
    cursor.execute(sql)
    tokens = cursor.fetchall()
    cursor.close()

    token = get_api_token("krasting@gmail.com")

    return render_template("examples-blank.html", tokens=tokens)


@dora.route("/admin/tokens/reset", methods=["GET"])
@login_required
def update_api_token():
    assert current_user.admin, "Admin privileges are required for this function"
    id = request.args.get("id")
    userprofile = User.get(id)

    args = {}
    args["email"] = userprofile.email
    args["created"] = datetime.datetime.now().isoformat()
    args["token"] = secrets.token_urlsafe()
    args["expires"] = "2099-12-31T23:59:59"

    # loop over keys and values to construct a SQL call
    keys = str(",").join([f"{x}" for x in list(args.keys())])
    keys = f"({keys})"
    vals = str(",").join([f"'{x}'" for x in list(args.values())])
    vals = f"({vals})"
    update = str(",").join([f"{k}='{v}'" for (k, v) in args.items()])
    sql = f"INSERT into tokens {keys} VALUES {vals} ON DUPLICATE KEY UPDATE {update}"

    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()

    return redirect(f"/admin/users/edit/{id}")
