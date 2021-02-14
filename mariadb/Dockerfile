FROM mariadb:latest

ENV MYSQL_ROOT_PASSWORD rootpassword
ENV MYSQL_DATABASE mdt_tracker
ENV MYSQL_USER mdtadmin
ENV MYSQL_PASSWORD adminpassword

EXPOSE 3306

COPY default_schema.sql /docker-entrypoint-initdb.d/default_schema.sql

COPY bootstrap_experiments.sql bootstrap_experiments.sql
RUN cat bootstrap_experiments.sql >> /docker-entrypoint-initdb.d/default_schema.sql

COPY bootstrap_parameters.sql bootstrap_parameters.sql
RUN cat bootstrap_parameters.sql >> /docker-entrypoint-initdb.d/default_schema.sql

COPY bootstrap_project_map.sql bootstrap_project_map.sql
RUN cat bootstrap_project_map.sql >> /docker-entrypoint-initdb.d/default_schema.sql

COPY bootstrap_projects.sql bootstrap_projects.sql
RUN cat bootstrap_projects.sql >> /docker-entrypoint-initdb.d/default_schema.sql

RUN chmod ugo+rx /docker-entrypoint-initdb.d/default_schema.sql
