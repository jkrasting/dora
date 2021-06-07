FROM mariadb:latest

ENV MYSQL_ROOT_PASSWORD rootpassword
ENV MYSQL_DATABASE mdt_tracker
ENV MYSQL_USER mdtadmin
ENV MYSQL_PASSWORD adminpassword

EXPOSE 3306

RUN echo "CREATE DATABASE IF NOT EXISTS legacy;" > /docker-entrypoint-initdb.d/default_schema.sql
RUN echo "USE legacy;" >> /docker-entrypoint-initdb.d/default_schema.sql

COPY legacy.sql legacy.sql
RUN cat legacy.sql >> /docker-entrypoint-initdb.d/default_schema.sql

COPY default_schema.sql default_schema.sql
RUN cat default_schema.sql >> /docker-entrypoint-initdb.d/default_schema.sql

COPY bootstrap_experiments.sql bootstrap_experiments.sql
RUN cat bootstrap_experiments.sql >> /docker-entrypoint-initdb.d/default_schema.sql

COPY bootstrap_parameters.sql bootstrap_parameters.sql
RUN cat bootstrap_parameters.sql >> /docker-entrypoint-initdb.d/default_schema.sql

COPY bootstrap_project_map.sql bootstrap_project_map.sql
RUN cat bootstrap_project_map.sql >> /docker-entrypoint-initdb.d/default_schema.sql

COPY bootstrap_projects.sql bootstrap_projects.sql
RUN cat bootstrap_projects.sql >> /docker-entrypoint-initdb.d/default_schema.sql

COPY bootstrap_users.sql bootstrap_users.sql
RUN cat bootstrap_users.sql >> /docker-entrypoint-initdb.d/default_schema.sql

RUN chmod ugo+rx /docker-entrypoint-initdb.d/default_schema.sql
