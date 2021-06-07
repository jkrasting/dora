FROM krasting/dorabase:dev as server

RUN pip install git+https://github.com/raphaeldussin/static_downsampler
RUN pip install git+https://github.com/raphaeldussin/xoverturning
RUN pip install git+https://github.com/jkrasting/gfdlvitals@dev
RUN pip install git+https://github.com/jkrasting/om4labs@dev
RUN pip install git+https://github.com/jkrasting/MOM6_parameter_scanner.git
RUN pip install git+https://github.com/jkrasting/xcompare

FROM server

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
