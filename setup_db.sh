#!/bin/bash
set -e

HBA="/etc/postgresql/16/main/pg_hba.conf"

# Переключаем pg_hba на trust для postgres локально
sed -i 's/^local   all             postgres.*/local   all             postgres                                trust/' "$HBA"
pg_ctlcluster 16 main reload

sleep 1

# Устанавливаем пароль postgres
psql -U postgres -c "ALTER USER postgres WITH PASSWORD '12814948';" postgres

# Создаём БД minitms если не существует
psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname='minitms'" postgres \
  | grep -q 1 || psql -U postgres -c "CREATE DATABASE minitms OWNER postgres;" postgres

# Возвращаем pg_hba к md5
sed -i 's/^local   all             postgres                                trust/local   all             postgres                                md5/' "$HBA"
pg_ctlcluster 16 main reload

echo "=== DONE ==="
psql -U postgres -lqt postgres | cut -d'|' -f1 | grep minitms
