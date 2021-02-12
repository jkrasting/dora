#!/usr/bin/env python

# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from dotenv import load_dotenv
from OpenSSL import SSL

context = SSL.Context(SSL.TLSv1_2_METHOD)
context.use_privatekey_file("certs/key.pem")
context.use_certificate_file("certs/cert.pem")

from app import app

if __name__ == "__main__":
    load_dotenv(".env")
    context = ("certs/cert.pem", "certs/key.pem")
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=context)
