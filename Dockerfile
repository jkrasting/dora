FROM python:3.8

RUN apt-get install -y libmysqlclient-dev

ENV FLASK_APP run.py

COPY run.py gunicorn-cfg.py requirements.txt ./
COPY app app

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["gunicorn","--preload","--certfile", "/etc/certificates/cert.pem", "--keyfile", "/etc/certificates/key.pem", "--config", "gunicorn-cfg.py", "run:app"]
