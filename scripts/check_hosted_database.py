"""Read-only hosted login probe using the operator's encrypted local credentials."""
import argparse
import json
import os
import subprocess
import sys
from dataclasses import replace

from services.worker.local_credentials import ROLES


class ProbeError(Exception):
    pass


def check_role(role, *, pilot_profile=False):
    from services.worker.local_credentials import database_config
    from services.worker.database_transport import connect
    try:
        config = database_config(role)
        if pilot_profile:
            config = replace(config,connect_timeout=10)
    except Exception:
        raise ProbeError('local_credentials_unavailable') from None
    expected = 'gather_ingestion_coordinator' if role=='gather_admission' else 'gather_ingestion_worker'
    # Admission identity is a non-user sentinel for connection checks only.
    # No document operation or admission is performed under this identity.
    owner = '00000000-0000-0000-0000-000000000000' if role=='gather_admission' else None
    try:
        connection = connect(config,owner)
    except Exception as error:
        state = getattr(error,'pgcode',None)
        code = 'database_authentication_failed' if state in ('28000','28P01') else 'database_connection_failed'
        raise ProbeError(code) from None
    try:
        with connection.cursor() as cursor:
            cursor.execute('select current_user')
            if cursor.fetchone()!=(expected,) or not connection.info.ssl_in_use:
                raise ValueError('connection_policy_mismatch')
        return {'role':role,'tls':True,'restricted_role':expected,'connected':True}
    finally:
        try:
            connection.rollback()
        finally:
            connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--role',choices=ROLES)
    parser.add_argument('--pilot-profile',action='store_true',help='Use the approved 15-second total / 10-second connect pilot profile')
    parser.add_argument('--child-role',choices=ROLES,help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child_role:
        try:
            print(json.dumps(check_role(args.child_role,pilot_profile=args.pilot_profile)))
        except Exception as error:
            code = str(error) if isinstance(error,ProbeError) else 'connection_policy_check_failed'
            print(json.dumps({'role':args.child_role,'connected':False,'error':code}))
            sys.exit(1)
        return
    if not args.run:
        print('Preview: verify both stored logins with TLS; no document or job operations. Add --run.')
        return
    from services.worker.database_transport import ROOT
    for role in ((args.role,) if args.role else ROLES):
        try:
            result = subprocess.run([sys.executable,'-I','-B','-c',
                f'import sys; sys.path.insert(0,{str(ROOT)!r}); from scripts.check_hosted_database import main; main()',
                '--child-role',role,*(['--pilot-profile'] if args.pilot_profile else [])],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,cwd=ROOT,
                env={k:os.environ[k] for k in ('SYSTEMROOT','WINDIR') if k in os.environ},timeout=15 if args.pilot_profile else 5)
            if len(result.stdout)>4096:
                raise ValueError()
            value = json.loads(result.stdout)
            if result.returncode or value.get('connected') is not True:
                allowed = {'local_credentials_unavailable','database_authentication_failed',
                           'database_connection_failed','connection_policy_check_failed'}
                code = value.get('error')
                print(json.dumps({'role':role,'connected':False,'error':code if code in allowed else 'probe_failed'}))
                raise ValueError()
            print(json.dumps(value))
        except subprocess.TimeoutExpired:
            raise SystemExit('Read-only connection deadline exceeded for '+role+'. No automatic retry; no document/job changes.') from None
        except Exception:
            raise SystemExit('Read-only connection check failed for '+role+'. No automatic retry; no document/job changes.') from None


if __name__=='__main__':
    main()
