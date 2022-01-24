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
dora = Flask(__name__)
dora.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
dora.config["TESTING"] = True
dora.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Import routing to render the pages
from dora import views
