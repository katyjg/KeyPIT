FROM python:3.7-alpine

MAINTAINER Kathryn Janzen <kathryn.janzen@lightsource.ca>

COPY requirements.txt /

RUN apk add --no-cache --virtual .build-deps bash gcc linux-headers musl-dev postgresql-dev libpq libffi-dev \
    apache2-mod-wsgi python3-dev libxml2-dev libxslt-dev

RUN set -ex && /usr/bin/pip3 install --upgrade pip && /usr/bin/pip3 install --no-cache-dir -r /requirements.txt

EXPOSE 80

ADD . /keypit
ADD ./local /keypit/local

COPY deploy/run-server.sh /run-server.sh
COPY deploy/wait-for-it.sh /wait-for-it.sh
RUN chmod -v +x /run-server.sh /wait-for-it.sh

COPY deploy/keypit.conf /etc/apache2/conf.d/zzzkeypit.conf

RUN /usr/bin/python3 /keypit/manage.py collectstatic --noinput

CMD /run-server.sh
