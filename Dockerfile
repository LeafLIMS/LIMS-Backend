# Suggest running this as 'app'
# Before running, the database server ('db') must first be started

FROM python:3.5
ENV PYTHONUNBUFFERED 1
ENV DJANGO_CONFIGURATION Docker

ENV HOME /root
RUN apt-get update
RUN apt-get install -y wget
RUN wget -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" > /etc/apt/sources.list.d/pgdg.list
RUN apt-get update
RUN apt-get install -y postgresql-client-9.3

WORKDIR /usr/src/app
RUN mkdir lims
COPY . lims

WORKDIR /usr/src/app/lims
RUN pip install -r requirements.txt

ENV DB_NAME postgres
# ENV DB_PASSWORD password
ENV DB_USER postgres
ENV DB_HOST db 
ENV DB_PORT 5432
ENV SALESFORCE_USERNAME none 
ENV SALESFORCE_PASSWORD none
ENV SALESFORCE_TOKEN none
ENV PROJECT_IDENTIFIER_PREFIX GM
ENV PROJECT_IDENTIFIER_START 100
ENV LISTEN_HOST 0.0.0.0
ENV LISTEN_PORT 8000

CMD ["sh", "-c", "gunicorn lims.wsgi -w 2 -b $LISTEN_HOST:$LISTEN_PORT --log-level -"]

