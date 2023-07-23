import psutil

from .user import User

from flask import g

from dora import dora
from flask import request
from flask import render_template
from flask import session
from flask import redirect

from flask_login import current_user, login_required

@dora.route("/admin/restart")
@login_required
def restart_container():
    assert current_user.admin, "Admin privileges are required for this function"
    id = request.args.get("id")
    userprofile = User.get(id)
    for proc in psutil.Process(1).children(recursive=True):
        proc.kill()

    return render_template(
        "page-500.html", msg=f"Yarr! Dora be consigned to Davy Jones' Locker!"
    )
