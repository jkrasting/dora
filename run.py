#!/usr/bin/env python

# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)