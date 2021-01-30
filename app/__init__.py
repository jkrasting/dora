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

# Configuration
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.config["TESTING"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Import routing to render the pages
from app import views
