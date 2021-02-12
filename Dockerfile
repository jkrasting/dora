FROM continuumio/miniconda3 as conda_sql

RUN apt-get install -y libmariadb-dev

FROM conda_sql as environment

# Create the environment:
COPY environment.yml .
RUN conda env create -f environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "env", "/bin/bash", "-c"]

FROM environment

# Make sure the environment is activated:
RUN echo "Make sure flask is installed:"
RUN python -c "import flask"

# The code to run when container is started:

ENV FLASK_APP run.py

COPY run.py gunicorn-cfg.py ./
COPY app app

EXPOSE 5000
CMD ["gunicorn","--preload","--certfile", "/etc/certificates/cert.pem", "--keyfile", "/etc/certificates/key.pem", "--config", "gunicorn-cfg.py", "run:app"]
