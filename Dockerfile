# Base Docker Container for Dora
# ==============================

FROM condaforge/miniforge3:latest

# Update OS packages
RUN apt update \
    && apt -y upgrade \
    && apt -y install vim mysql-client

# Create the environment:
COPY envs envs
RUN mamba env create -f envs/env.prod.yml \
  && conda clean --all \
  && echo "conda activate env" >> ~/.bashrc

# ENV PATH /opt/conda/envs/env/bin:$PATH

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
