import os
import json
import requests
from datetime import datetime
from datetime import timedelta

from dora import dora
from dora.user import User
from oauthlib.oauth2 import WebApplicationClient

from flask_login import LoginManager
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from flask import request
from flask import redirect
from flask import url_for

# Global
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

login_manager = LoginManager()
login_manager.init_app(dora)
client = WebApplicationClient(GOOGLE_CLIENT_ID)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@dora.route("/protected.html")
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


@dora.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )

    return redirect(request_uri)


@dora.route("/login/callback")
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
        try:
            User.create(
                unique_id, users_name, users_email, picture, remote_addr, login_date
            )
        except Exception as exc:
            if "Duplicate entry" in str(exc):
                User.reset(
                    unique_id, users_name, users_email, picture, remote_addr, login_date
                )
            else:
                raise exc
    else:
        User.update(
            unique_id, users_name, users_email, picture, remote_addr, login_date
        )

    login_user(user, remember=False)

    return redirect(url_for("index"))


@dora.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
