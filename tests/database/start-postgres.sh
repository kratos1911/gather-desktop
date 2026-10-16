#!/bin/sh
# Disposable test database only. No vendor bootstrap or production role changes.
set -eu
initdb -D "$PGDATA" --username=postgres --auth=trust --encoding=UTF8 --locale=C > /tmp/gather-init.log
if [ -f /gather-init.sql ]; then
  # Disposable API harness only: three service roles on its directly connected
  # private Docker network. The database has no published host port.
  printf '%s\n' 'host postgres authenticator,supabase_auth_admin,supabase_storage_admin samenet trust' >> "$PGDATA/pg_hba.conf"
  pg_ctl -D "$PGDATA" -o "-k /tmp -p 5433 -h '' -c shared_buffers=16MB" -l /tmp/gather-bootstrap.log -w start
  psql -X -p 5433 -U postgres -v ON_ERROR_STOP=1 -f /gather-init.sql
  pg_ctl -D "$PGDATA" -m fast -w stop
fi
exec postgres -D "$PGDATA" -k /tmp -h '*' -c shared_buffers=16MB
