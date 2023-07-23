# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import datetime
import json
import lxml
import os
import pymysql
import requests
import sqlite3
import traceback
import yaml
import subprocess
import warnings
import io
import gfdlvitals
import xarray as xr

import flask


from flask import (
    g,
    Flask,
    Response,
    redirect,
    render_template,
    request,
    send_from_directory,
    send_file,
    url_for,
)


from flask_login import current_user

from jinja2 import TemplateNotFound
from dora.user import User

from .xml import parse_xml

from .om4 import *
from .diffmaps import *
from .auth import *
from .api import *
from .extpkg import *
from .globals import *
from .paramdiff import *
from .projects import *
from .experiments import *
from .scalar import *
from .stats import *
from .user import user_experiment_count, check_sql_table_exists, create_tokens_table
from .logging import create_error_log_table
from .usertools import *
from .tokentools import *
from .restart import *
from .parameters import *

# App modules
from dora import dora

from werkzeug.utils import secure_filename

# load mailer
if dora.config["DO_MAIL"]:
    from flask_mail import Mail, Message

    mail = Mail(dora)


# as a decorator
@dora.errorhandler(500)
def internal_server_error(e):
    return render_template("page-500.html"), 500


@dora.errorhandler(Exception)
def special_exception_handler(error):
    errormsg = str(error)
    print(errormsg)
    if current_user.is_authenticated:
        username = current_user.email
        if current_user.admin:
            tbstr = traceback.format_exc()
        else:
            tbstr = ""
    else:
        username = None
        tbstr = ""

    details = {
        "timestamp": datetime.datetime.now().isoformat(),
        "ip": request.remote_addr,
        "hostname": None,
        "username": username,
        "url": request.url,
        "error": errormsg,
        "traceback": traceback.format_exc(),
    }

    details = {k: v for k, v in details.items() if v is not None}

    keys, values = list(zip(*details.items()))
    keys = str(tuple([str(x) for x in keys])).replace("'", "")
    values = str(tuple([str(x) for x in values]))
    sql = f"insert into logs {keys} values {values}"
    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()

    return render_template(
        "page-500-unspec.html",
        msg=f"Dora encountered an exception: {errormsg}",
        tbstr=tbstr,
    )


with dora.app_context():
    db = get_db()
    cursor = db.cursor()
    if not check_sql_table_exists("tokens", cursor):
        create_tokens_table(db, cursor)
    if not check_sql_table_exists("logs", cursor):
        create_error_log_table(db, cursor)
    #else:
    #    print("Resetting existing logs table")
    #    sql = "DROP TABLE `logs`;"
    #    cursor.execute(sql)
    #    db.commit()
    #    create_error_log_table(db, cursor)
    cursor.close()


@dora.before_request
def before_request():
    flask.session.permanent = True
    dora.permanent_session_lifetime = datetime.timedelta(hours=10)
    flask.session.modified = False


# App main route + generic routing
@dora.route("/", defaults={"path": "index.html"}, methods=["GET"])
@dora.route("/<path>", methods=["GET"])
def index(path):
    try:
        # Serve the file (if exists) from dora/templates/FILE.html
        if current_user.is_authenticated:
            user_params = {
                "username": current_user.name,
                "userpic": current_user.profile_pic,
            }
        else:
            user_params = {"username": "", "userpic": ""}

        try:
            result = render_template(path, **user_params)
        except Exception as e:
            return "Site is under maintenance. " + str(e)

        return result

    except TemplateNotFound:
        return render_template("page-404.html"), 404


@dora.route("/err")
def test_exception():
    raise ValueError("some test error")
    return "Success."


@dora.route("/profile/")
@login_required
def show_user():
    username = current_user.firstlast
    numexp = user_experiment_count(username)
    db = get_db()
    cursor = db.cursor()
    sql = f"SELECT id,expName from master where userName='{username}' or owner='{username}'"
    cursor.execute(sql)
    result = cursor.fetchall()
    print(current_user.firstlast)
    return render_template(
        "profile.html", numexp=numexp, tables=["aaa"], experiments=result
    )


@dora.route("/backup")
def dump_database():
    cmd = f"mysqldump {os.environ['DB_DATABASE']} -h {os.environ['DB_HOSTNAME']} -u {os.environ['DB_USERNAME']} --password={os.environ['DB_PASSWORD']}"
    output = subprocess.check_output(cmd.split(" "))
    output = output.decode()
    return Response(output, mimetype="text/plain")

@dora.route("/dldb", methods=['GET'])
def dump_gfdlvitals_nc():
    filestub = request.args.get("file")
    dl_name = request.args.get("dl_name")
    def set_encoding(my_ds, my_attr):
      for var in getattr(my_ds, my_attr):
        if '_FillValue' not in my_ds[var].encoding.keys():
          my_ds[var].encoding['_FillValue'] = None
        if var == 'time':
          continue
        my_ds[var].attrs = db[var].attrs
        remove = []
        for k, v in my_ds[var].attrs.items():
          if v is None:
            remove.append(k)
        for rm in remove:
          del my_ds[var].attrs[rm]
      return my_ds

    db = gfdlvitals.open_db(filestub)
    ds = xr.Dataset.from_dataframe(db)
    ds = ds.rename({'index': 'time'})
    ds = set_encoding(ds, "data_vars")
    ds = set_encoding(ds, "coords")
    return send_file(io.BytesIO(ds.to_netcdf()), as_attachment=True, download_name=dl_name)


@login_required
@dora.route("/restore", methods=['GET'])
def upload_file():

    if not current_user.admin:
        return "You must be an admin to use this feature."

    filestub = request.args.get("file")
    file = secure_filename(filestub)
    trusted_backup_directory = os.getenv("TRUSTED_BACKUP_DIR")
    file = os.path.join(trusted_backup_directory, file)

    if not os.path.exists(file):
        raise ValueError(f"Unable to find file: {file}")

    db = get_db()
    cursor = db.cursor()
    
    sql = f"SELECT table_name from information_schema.tables WHERE table_schema = '{os.getenv('DB_DATABASE')}'"
    cursor.execute(sql)
    table_names = cursor.fetchall()

    for name_dict in table_names:
        table_name = name_dict['table_name']
        drop_statement = f"DROP TABLE IF EXISTS `{table_name}`;"
        print(drop_statement)
        cursor.execute(drop_statement)

    db.commit()
    db.close()

    cmd = f"mysql --host={os.getenv('DB_HOSTNAME')} --user={os.getenv('DB_USERNAME')} --password={os.getenv('DB_PASSWORD')} --database={os.getenv('DB_DATABASE')} < {file}"
    subprocess.run(cmd, shell=True, check=True)
    return Response("Success", mimetype="text/plain")


@login_required
@dora.route("/mailer")
def simple_mailer():
    action = {}

    if not current_user.admin:
        return "You must be an admin to use this feature."

    mailto = request.args.get("mailto")
    if mailto is None:
        return "Destination not specified.  Use `mailto` cgi to specify address"
    else:
        action["mailto"] = mailto

    if dora.config["DO_MAIL"] is False:
        result = "Mail is not enabled. Set `DO_MAIL` to True."
    else:
        mail_config_items = [
            "MAIL_SERVER",
            "MAIL_USE_SSL",
            "MAIL_USE_TLS",
            "MAIL_PORT",
            "MAIL_USERNAME",
            "MAIL_PASSWORD",
            "MAIL_DEFAULT_SENDER",
        ]
        mail_config_items = {
            k: v for k, v in dora.config.items() if k in mail_config_items
        }
        if mail_config_items["MAIL_PASSWORD"] is not None:
            mail_config_items["MAIL_PASSWORD"] = "*" * len(
                mail_config_items["MAIL_PASSWORD"]
            )

        result = {**mail_config_items, **action}

        msg = Message("Test email from Dora.", recipients=[action["mailto"]])
        msg.body = "This is an automatic test email message from the Dora system"
        mail.send(msg)

        result["status"] = "message sent"

    return result


@dora.teardown_appcontext
def teardown_db(exception):
    db = g.pop("db", None)

    if db is not None:
        try:
            db.close()
        except Exception as exc:
            warnings.warn("Unable to teardown database connection.")


if __name__ == "__main__":
    dora.run(ssl_context="adhoc")
