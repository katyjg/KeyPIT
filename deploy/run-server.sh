#!/bin/bash

export SERVER_NAME=${SERVER_NAME:-$(hostname --fqdn)}

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
