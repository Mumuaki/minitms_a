#!/bin/bash
set -e
# Включаем listen_addresses = '*'
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/16/main/postgresql.conf
# Перезапускаем PostgreSQL  
pg_ctlcluster 16 main restart
echo "LISTEN_OK"
grep "listen_addresses" /etc/postgresql/16/main/postgresql.conf | grep -v "^#"
