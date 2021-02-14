#!/bin/sh

# load environment variables 
`sed -e "s/^/export /g" .env`

# start server
exec gunicorn --preload --certfile /etc/certificates/cert.pem --keyfile /etc/certificates/key.pem --config gunicorn-cfg.py run:app
