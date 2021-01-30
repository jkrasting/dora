# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

dbhost = "127.0.0.1"
dbport = 3306

import json
import lxml
import os
import pymysql
import requests
import sqlite3
import yaml

from flask import (
    g,
    Flask,
    Response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from jinja2 import TemplateNotFound
from datetime import datetime
from oauthlib.oauth2 import WebApplicationClient
from app.user import User

from .xml import parse_xml
from .Experiment import Experiment
from .db import get_db
from .projects import *
from .experiments import *
from .scalar import *

# App modules
from app import app

# Global
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

login_manager = LoginManager()
login_manager.init_app(app)

model_types = sorted(
    [
        "CM4",
        "OM4",
        "AM4",
        "CM4p5",
        "ESM4p5",
        "ESM4",
        "ESM2G",
        "OM4p5",
        "CM3",
        "LM3",
        "SPEAR",
        "SM4",
        "CMIP6-CM4",
        "LM4",
        "OM4p125",
        "CMIP6-ESM4",
        "C4MIP-ESM4",
    ]
)

cmip6_mips = sorted(
    [
        "AerChemMIP",
        "CDRMIP",
        "C4MIP",
        "CFMIP",
        "DECK",
        "DAMIP",
        "FAFMIP",
        "GMMIP",
        "LUMIP",
        "OMIP",
        "RFMIP",
        "SIMIP",
        "ScenarioMIP",
    ]
)

client = WebApplicationClient(GOOGLE_CLIENT_ID)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.context_processor
def get_global_vars():
    return {
        "model_types": model_types,
        "cmip6_mips": cmip6_mips,
        "projects": list_projects(),
    }


# App main route + generic routing
@app.route("/", defaults={"path": "index.html"}, methods=["GET"])
@app.route("/<path>", methods=["GET"])
def index(path):
    try:
        # Serve the file (if exists) from app/templates/FILE.html
        if current_user.is_authenticated:
            user_params = {
                "username": current_user.name,
                "userpic": current_user.profile_pic,
            }
        else:
            user_params = {"username": "", "userpic": ""}
        return render_template(path, **user_params)

    except TemplateNotFound:
        return render_template("page-404.html"), 404


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
        scope=["openid", "email", "profile"],
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
        code=code,
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
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
        if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
            remote_addr = request.environ["REMOTE_ADDR"]
        else:
            remote_addr = request.environ["HTTP_X_FORWARDED_FOR"]
        print("Remote address: ", remote_addr)
        login_date = str(datetime.now().isoformat())
    else:
        return "User email not available or not verified", 400

    user = User(
        id_=unique_id,
        name=users_name,
        email=users_email,
        profile_pic=picture,
        remote_addr=remote_addr,
        login_date=login_date,
    )

    if not User.get(unique_id):
        print(
            "params: ",
            unique_id,
            users_name,
            users_email,
            picture,
            remote_addr,
            login_date,
        )
        User.create(
            unique_id, users_name, users_email, picture, remote_addr, login_date
        )
    else:
        User.update(
            unique_id, users_name, users_email, picture, remote_addr, login_date
        )

    login_user(user)

    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(ssl_context="adhoc")


@app.route("/cvdp/<project_id>")
def view_cvdp_root(project_id):
    path = "/cvdp_path"
    return redirect(f"/cvdp/{project_id}/index.html", 302)


@app.route("/cvdp/<project_id>/<path:filename>")
def view_cvdp(project_id, filename):
    path = "/cvdp_path"
    if not os.path.exists(path + filename):
        return render_template("page-404.html"), 404
    else:
        return send_from_directory(path, filename)


@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop("db", None)

    if db is not None:
        db.close()
