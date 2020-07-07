#!/bin/bash

export SERVER_NAME=${SERVER_NAME:-$(hostname --fqdn)}
export CERT_PATH=${CERT_PATH:-/etc/letsencrypt/live/${SERVER_NAME}}

# create key if none present
CERT_KEY=${CERT_PATH}/privkey.pem
if [ ! -f $CERT_KEY ]; then
    export CERT_PATH = '/certs'
    CERT_KEY=${CERT_PATH}/privkey.pem
    mkdir -p ${CERT_PATH}
    openssl req -x509 -nodes -newkey rsa:2048 -keyout ${CERT_KEY} -out ${CERT_PATH}/fullchain.pem -subj '/CN=${SERVER_NAME}'
fi

# Make sure we're not confused by old, incompletely-shutdown httpd
# context after restarting the container.  httpd won't start correctly
# if it thinks it is already running.
rm -rf /run/httpd/* /tmp/httpd*

./wait-for-it.sh keypit-db:5432 -t 60 &&

if [ ! -f /keypit/local/.dbinit ]; then
    /usr/bin/python3 /keypit/manage.py migrate --noinput &&
    touch /keypit/local/.dbinit
    chown -R apache:apache /keypit/local/media
else
    /usr/bin/python3 /keypit/manage.py migrate --noinput
fi

# create log directory if missing
if [ ! -d /keypit/local/logs ]; then
    mkdir -p /keypit/local/logs
fi


exec /usr/sbin/httpd -DFOREGROUND -e debug
