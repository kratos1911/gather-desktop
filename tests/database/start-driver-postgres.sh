#!/bin/sh
# Dedicated disposable driver test only; no admin TCP login.
set -eu
initdb -D "$PGDATA" --username=postgres --auth=trust --encoding=UTF8 --locale=C > /tmp/gather-init.log
printf '%s\n' 'local all all trust' \
  'host postgres gather_admission,gather_worker all scram-sha-256' \
  'host all all all reject' > "$PGDATA/pg_hba.conf"
exec postgres -D "$PGDATA" -k /tmp -h '*' -c shared_buffers=16MB
