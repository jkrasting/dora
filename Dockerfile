FROM krasting/dorabase as server

RUN pip install git+https://github.com/raphaeldussin/static_downsampler
RUN pip install git+https://github.com/jkrasting/cmip_basins
RUN pip install git+https://github.com/jkrasting/gfdlvitals
RUN pip install git+https://github.com/raphaeldussin/om4labs
RUN pip install git+https://github.com/jkrasting/MOM6_parameter_scanner.git

FROM server

# Make sure the environment is activated:
RUN echo "Make sure flask is installed:"
RUN python -c "import flask"

# The code to run when container is started:

ENV FLASK_APP run.py

COPY run.py gunicorn-cfg.py ./
COPY certs /etc/certificates
COPY app app
COPY .env .env

COPY run_gunicorn.sh run_gunicorn.sh
RUN chmod +x run_gunicorn.sh

EXPOSE 5000

CMD ["/bin/bash", "run_gunicorn.sh"]
