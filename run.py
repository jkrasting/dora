#!/usr/bin/env python

# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import sys
from dotenv import load_dotenv
from OpenSSL import SSL

HOST = "0.0.0.0"
PORT = 5050

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "dev":
            load_dotenv(".devenv")
            print("We are here")
            print(os.environ.keys())
            from dora import dora
            dora.run(host=HOST, port=PORT, debug=True, ssl_context="adhoc")
        elif sys.argv[1] == "nossl":
            load_dotenv(".devenv")
            from dora import dora
            dora.run(host=HOST, port=PORT, debug=True)
        elif sys.argv[1] == "localcert":
            load_dotenv(".devenv")
            context = SSL.Context(SSL.TLSv1_2_METHOD)
            context.use_privatekey_file("certs/key.pem")
            context.use_certificate_file("certs/cert.pem")
            context = ("certs/cert.pem", "certs/key.pem")
            from dora import dora
            dora.run(host=HOST, port=PORT, debug=True, ssl_context=context)
    else:
        from dora import dora
        dora.run(ssl_context="adhoc", host=HOST, port=PORT, debug=True)
