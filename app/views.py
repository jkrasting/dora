# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

dbhost = "127.0.0.1"
dbport = 3306

import json
import sqlite3
import pymysql
import os
import yaml

from flask import (
    Flask, 
    Response,
    redirect, 
    render_template,
    request, 
    url_for
)

from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user    
)

from jinja2 import TemplateNotFound

from datetime import datetime

from .db import get_db

from oauthlib.oauth2 import WebApplicationClient
import requests

from app.user import User

from flask import g
import base64
import io
import gfdlvitals

import matplotlib.pyplot as plt
plt.switch_backend("Agg")

# App modules
from app import app

# Global 
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

login_manager = LoginManager()
login_manager.init_app(app)

#try:
#    init_db_command()
#except sqlite3.OperationalError:
#    pass

client = WebApplicationClient(GOOGLE_CLIENT_ID)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def stream_template(template_name, **context):
    ## possibly needed, broke with login:
    ##     app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv

# App main route + generic routing
@app.route('/', defaults={'path': 'index.html'}, methods=["GET"])
@app.route('/<path>', methods=['GET'])
def index(path):
    try:
        # Serve the file (if exists) from app/templates/FILE.html
        if current_user.is_authenticated:
            user_params = {"username":current_user.name, 
                "userpic":current_user.profile_pic,
            }
        else:
            user_params = {"username":"","userpic":""}
        return render_template( path , **user_params)
    
    except TemplateNotFound:
        return render_template('page-404.html'), 404

@app.route("/protected.html")
def protected():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {} </p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img>'
            '<a class="button" href="/logout">Logout</a>'.format(
            current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", 'profile']
    )

    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID,GOOGLE_CLIENT_SECRET)
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["name"]
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            remote_addr = request.environ['REMOTE_ADDR']
        else:
            remote_addr = request.environ['HTTP_X_FORWARDED_FOR']
        print("Remote address: ",remote_addr)
        login_date = str(datetime.now().isoformat())
    else:
        return "User email not available or not verified", 400

    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture, remote_addr=remote_addr, login_date=login_date
    )

    if not User.get(unique_id):
        print("params: ",unique_id, users_name, users_email, picture, remote_addr, login_date)
        User.create(unique_id, users_name, users_email, picture, remote_addr, login_date)
    else:
        User.update(unique_id, users_name, users_email, picture, remote_addr, login_date)

    login_user(user)

    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(ssl_context="adhoc")

@app.route("/admin/project/<project_id>")
def project(project_id,params={"project_description":"","project_name":"","project_config":""}):
    params["project_id"] = project_id
    if project_id != "new": 
        db = get_db()
        cursor = db.cursor()
        sql = f"select * from projects where project_id={project_id}"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        params = result if isinstance(result,dict) else params
        #print(yaml.load(params["project_config"]))
    #D = {"main":{"label":"Main table of experiments","sql":"SELECT * from experiments where ID=890"}}
    #print(yaml.dump(D))
    #content['project_config'] = yaml.dump(D)
    content = {}
    content['project_id'] = params["project_id"]
    content['project_name'] = params["project_name"]
    content['project_description'] = params["project_description"]
    content['project_config'] = params["project_config"]
    return render_template("project.html", **content)

@app.route("/admin/project_update.html")
def project_update():
    args = dict(request.args)

    db = get_db()
    cursor = db.cursor()
    sql = 'select AUTO_INCREMENT from information_schema.TABLES where TABLE_SCHEMA = "mdt_tracker" and TABLE_NAME = "projects"'
    cursor.execute(sql)
    nextid = cursor.fetchone()['AUTO_INCREMENT']

    if args["project_id"] == "new":
        args["project_id"] = nextid
    
    if int(args["project_id"]) >  int(nextid):
        return render_template('page-500.html',msg="Project ID is too high.")
    keys = str(",").join([f"{x}" for x in list(args.keys())])
    keys = f"({keys})"
    vals = str(",").join([f"'{x}'" for x in list(args.values())])
    vals = f"({vals})"
    update = str(",").join([f"{k}='{v}'" for (k,v) in args.items()])
    sql = f"INSERT into projects {keys} VALUES {vals} ON DUPLICATE KEY UPDATE {update}"
    cursor.execute(sql)
    db.commit()
    cursor.close()
    return render_template("success.html", msg="Updated project successfully.")


@app.route("/scalar-diags.html")
def scalardiags():

    idnum = request.args.getlist("id")
    idnum = None if len(idnum) == 0 else idnum

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
        return render_template( "scalar-menu.html" )

    fname = f"/Users/krasting/dbverif5/new/{region}Ave{realm}.db" 

    if os.path.exists(fname):
        dset = gfdlvitals.open_db(fname)
    else:
        msg = f"Unable to load SQLite file: {fname}"
        return render_template('page-500.html',msg=msg)

    def plot_gen():
        for x in sorted(list(dset.columns)):
            fig = gfdlvitals.plot_timeseries(dset,trend=trend,smooth=smooth,var=x,\
                  nyears=nyears,align_times=align,labels="Test")
            fig = fig[0]
            imgbuf = io.BytesIO()
            fig.savefig(imgbuf, format="png", bbox_inches="tight",dpi=72)
            plt.close(fig)
            imgbuf.seek(0)
            uri = 'data:image/png;base64,' + base64.b64encode(imgbuf.getvalue()).decode('utf-8').replace('\n', '')
            yield uri

    content = {"rows":plot_gen(),"region":region.capitalize(),"realm":realm.capitalize()}
    return Response(stream_template("scalar-diags.html", **content ))

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()

# Some sample database code below
#    conn = pymysql.connect(host=dbhost,
#                           port=dbport,
#                           user="mdtadmin",
#                           password="adminpassword",
#                           db="mdt_tracker",
#                           cursorclass=pymysql.cursors.DictCursor)
#
#    cursor = conn.cursor()
#    sql = "SELECT * from master where id=890;"
#    _ = cursor.execute(sql)
#    result = cursor.fetchone()
#
#    print(sql)
#    print(result)
#
#    cursor.close()
#    conn.close()