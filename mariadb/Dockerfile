FROM mariadb:latest

ENV MYSQL_ROOT_PASSWORD rootpassword
ENV MYSQL_DATABASE mdt_tracker
ENV MYSQL_USER mdtadmin
ENV MYSQL_PASSWORD adminpassword

EXPOSE 3306

COPY default_schema.sql default_schema.sql
RUN cat default_schema.sql >> /docker-entrypoint-initdb.d/default_schema.sql

RUN chmod ugo+rx /docker-entrypoint-initdb.d/default_schema.sql
