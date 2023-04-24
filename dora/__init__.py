# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from datetime import timedelta

from . import db
from . import user

# import Flask
from flask import Flask
from flask_mail import Mail, Message

# Configuration
dora = Flask(__name__)

# dora.config["TESTING"] = True
dora.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
dora.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Mail server configuration
dora.config["DO_MAIL"] = (
    (os.getenv("DO_MAIL") == "True") if os.getenv("DO_MAIL") is not None else False
)

config = {}
config["MAIL_SERVER"] = "localhost"
config["MAIL_PORT"] = 25
config = {
    **config,
    **{k: os.getenv(k) for k in config.keys() if os.getenv(k) is not None},
}
for k, v in config.items():
    dora.config[k] = v

# Mail boolean option configuration
config = {}
config["MAIL_ASCII_ATTACHMENTS"] = False
config["MAIL_USE_TLS"] = False
config["MAIL_USE_SSL"] = False
config = {
    **config,
    **{k: (os.getenv(k) == "True") for k in config.keys() if os.getenv(k) is not None},
}
for k, v in config.items():
    dora.config[k] = v

# Mail username and password configuration
dora.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
dora.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
dora.config["MAIL_DEFAULT_SENDER"] = f"DORA <{os.getenv('MAIL_DEFAULT_SENDER')}>"
dora.config["MAIL_MAX_EMAILS"] = os.getenv("MAIL_MAX_EMAILS")


# Import routing to render the pages
from dora import views
