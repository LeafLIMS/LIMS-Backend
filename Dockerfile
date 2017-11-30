FROM python:3.5

ENV PYTHONUNBUFFERED 1
ENV DJANGO_CONFIGURATION Docker
ENV HOME /root

# Listen host/port configuration
ENV LISTEN_HOST=0.0.0.0
ENV LISTEN_PORT=8000
ENV REDIS_URL=redis://redis:6379

ENV DOCKERIZE_VERSION v0.3.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

# Grab libxml2 and libxslt as they are super useful
RUN apt-get update && apt-get -q -y install libxml2-dev libxslt-dev

WORKDIR /usr/src/app
RUN mkdir lims
COPY . lims
WORKDIR /usr/src/app/lims
RUN pip install -r requirements.txt

CMD ["sh", "-c", "gunicorn lims.wsgi -w 2 -b $LISTEN_HOST:$LISTEN_PORT --log-level -"]

