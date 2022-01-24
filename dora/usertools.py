from .db import get_db
from .user import User
from .user import user_experiment_count
from .project_util import *

from flask import g

from dora import dora
from flask import request
from flask import render_template


@dora.route("/admin/users")
def list_users():
    db = get_db()
    cursor = db.cursor()
    sql = "select name,email,id from users"
    cursor.execute(sql)
    users = cursor.fetchall()
    cursor.close()
    return render_template("user_list.html", users=users)


@dora.route("/admin/users/edit/<id>")
def show_user_props(id):
    userprofile = User.get(id)
    username = userprofile.firstlast
    numexp = user_experiment_count(username)
    db = get_db()
    cursor = db.cursor()
    sql = f"SELECT id,expName from master where userName='{username}' or owner='{username}'"
    cursor.execute(sql)
    experiments = cursor.fetchall()
    return render_template(
        "user_edit.html",
        userprofile=userprofile,
        numexp=numexp,
        experiments=experiments,
    )


@dora.route("/admin/users/update", methods=["POST"])
def update_user_perms():
    args = dict(request.form)
    id = args["id"]
    userprofile = User.get(id)
    project_list = [project[1] for project in list_projects()]
    for perm in ["perm_add", "perm_del", "perm_modify", "perm_view"]:
        if perm in list(args.keys()):
            _perm = request.form.getlist(perm)
            _perm = [_perm] if not isinstance(_perm, list) else _perm
            _perm = [x for x in _perm if x in project_list]
            _perm = [str(lookup_project_from_name(x)) for x in _perm]
            _perm = str(",").join(_perm)
            userprofile.update_permission(perm, _perm)
    admin = "1" if "admin" in list(args.keys()) else "0"
    userprofile.update_permission("admin", admin)
    return render_template("success.html", msg="Updated user permissions successfully.")
