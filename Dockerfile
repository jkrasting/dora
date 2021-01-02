FROM python:3.8

ENV FLASK_APP run.py


COPY run.py gunicorn-cfg.py requirements.txt ./
COPY app app

RUN pip install -r requirements.txt

EXPOSE 5005
CMD ["gunicorn","--certfile", "/etc/nginx/certs/cert.pem", "--keyfile", "/etc/nginx/certs/key.pem", "--config", "gunicorn-cfg.py", "run:app"]
