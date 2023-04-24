# Base Docker Container for Dora
# ==============================

FROM continuumio/miniconda3:master-alpine

# Update OS packages
RUN apk update \
  && apk add --no-cache git \
  && apk add --no-cache bash \
  && apk add --no-cache mysql-client

# Update conda channels and install mamba
RUN conda config --add channels conda-forge \
  && conda config --add channels krasting \
  && conda install -y mamba

# Create the environment:
COPY envs envs
RUN mamba env create -f envs/env.prod.yml \
  && conda clean --all \
  && echo "conda activate env" >> ~/.bashrc

ENV PATH /opt/conda/envs/env/bin:$PATH

# The code to run when container is started:
ENV FLASK_APP run.py
COPY run.py run.py
COPY certs certs
COPY gunicorn gunicorn
RUN chmod +x gunicorn/gunicorn-run.sh
EXPOSE 5050
COPY dora dora
COPY .env .env

CMD ["/bin/bash", "gunicorn/gunicorn-run.sh"]
