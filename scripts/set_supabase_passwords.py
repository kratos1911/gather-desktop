"""Operator-run password setup for the two fixed Gather logins. No secret files."""
import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'fatolholcjxpwocnpzws'
HOST = 'aws-0-ap-southeast-2.pooler.supabase.com'
CERT = ROOT/'output/supabase-cli/prod-ca-2021.crt'
ROLES = {'gather_admission':'gather_ingestion_coordinator',
         'gather_worker':'gather_ingestion_worker'}


def validate_passwords(values):
    if set(values) != {'postgres',*ROLES}:
        raise ValueError('invalid_password_input')
    for role,value in values.items():
        minimum = 1 if role=='postgres' else 24
        if not isinstance(value,str) or not minimum<=len(value)<=1024 or '\x00' in value:
            raise ValueError('invalid_password_for_'+role)
    if len(set(values.values())) != 3:
        raise ValueError('passwords_must_be_different')


def connect(role,password):
    import psycopg2
    return psycopg2.connect(host=HOST,port=5432,dbname='postgres',
        user=role+'.'+PROJECT,password=password,sslmode='verify-full',sslrootcert=str(CERT),
        connect_timeout=5,gssencmode='disable',application_name='gather-password-setup',
        options='-c search_path= -c statement_timeout=5000 -c lock_timeout=3000')


def verify_role(cursor,role):
    cursor.execute('select rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls '
                   'from pg_catalog.pg_roles where rolname=%s',(role,))
    if cursor.fetchone() != (True,False,False,False,False,False,False):
        raise ValueError('unexpected_role_privileges')
    cursor.execute('select parent.rolname from pg_catalog.pg_auth_members m '
                   'join pg_catalog.pg_roles parent on parent.oid=m.roleid '
                   'join pg_catalog.pg_roles child on child.oid=m.member where child.rolname=%s',(role,))
    if cursor.fetchall() != [(ROLES[role],)]:
        raise ValueError('unexpected_role_membership')


def child():
    from psycopg2.extensions import encrypt_password
    from psycopg2 import sql
    stage = 'read_input'
    committed = False
    commit_attempted = False
    try:
        raw = sys.stdin.buffer.read(16385)
        if len(raw)>16384:
            raise ValueError()
        values = json.loads(raw)
        validate_passwords(values)
        stage = 'admin_tls_connection'
        connection = connect('postgres',values['postgres'])
        try:
            with connection:
                with connection.cursor() as cursor:
                    stage = 'role_permissions'
                    for role in ROLES:
                        verify_role(cursor,role)
                    stage = 'password_transaction'
                    for role in ROLES:
                        verifier = encrypt_password(values[role],role,scope=connection,algorithm='scram-sha-256')
                        cursor.execute(sql.SQL('alter role {} password %s').format(sql.Identifier(role)),(verifier,))
                commit_attempted = True
            committed = True
        finally:
            connection.close()
        for role, target in ROLES.items():
            stage = role+'_tls_login'
            connection = connect(role,values[role])
            try:
                with connection:
                    with connection.cursor() as cursor:
                        verify_role(cursor,role)
                        cursor.execute(sql.SQL('set local role {}').format(sql.Identifier(target)))
                        cursor.execute('select current_user')
                        if cursor.fetchone() != (target,):
                            raise ValueError()
            finally:
                connection.close()
        print(json.dumps({'success':True,'passwords_committed':True,'logins_verified':list(ROLES)}))
    except Exception:
        outcome = True if committed else (None if commit_attempted else False)
        print(json.dumps({'success':False,'stage':stage,'passwords_committed':outcome}))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--apply',action='store_true')
    action.add_argument('--check-input',action='store_true',help='Validate hidden input only; no database connection')
    parser.add_argument('--child',action='store_true',help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        child()
        return
    if not args.apply and not args.check_input:
        print('Preview: set only gather_admission/gather_worker passwords on '+PROJECT+'. No connection made.')
        return
    if not CERT.is_file():
        raise SystemExit('Expected CA certificate is missing. No changes made.')
    warnings.simplefilter('error',getpass.GetPassWarning)  # Never fall back to echoed input.
    print('Target: '+PROJECT+' / Sydney. Save two distinct new passwords in your password manager first.')
    values = {'postgres':getpass.getpass('Existing Supabase DATABASE password (hidden): ')}
    for role in ROLES:
        value = getpass.getpass('New '+role+' password, at least 24 characters (hidden): ')
        if value != getpass.getpass('Confirm '+role+' password (hidden): '):
            raise SystemExit('Passwords do not match. No changes made.')
        values[role] = value
    try:
        validate_passwords(values)
    except ValueError as error:
        messages = {'passwords_must_be_different':'All three passwords must be different.'}
        messages.update({'invalid_password_for_'+role:
            ('Existing database password must not be empty.' if role=='postgres' else
             role+' password must contain at least 24 characters.')+' Maximum 1024 characters; no NUL characters.'
            for role in ('postgres',*ROLES)})
        values.clear()
        raise SystemExit(messages.get(str(error),'Invalid password input.')+' No database connection was made.') from None
    if args.check_input:
        values.clear()
        print('Input checks passed. No database connection or password change was made.')
        return
    try:
        result = subprocess.run([sys.executable,'-I','-B',str(Path(__file__).resolve()),'--child'],
            input=json.dumps(values).encode(),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            env={k:os.environ[k] for k in ('SYSTEMROOT','WINDIR') if k in os.environ},
            cwd=ROOT,timeout=30)
        if len(result.stdout)>4096:
            raise ValueError()
        print(result.stdout.decode('utf-8'))
        sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        raise SystemExit('Setup deadline exceeded. Password update outcome is uncertain; do not retry automatically.') from None
    finally:
        values.clear()


if __name__=='__main__':
    try:
        main()
    except (Exception,KeyboardInterrupt):
        raise SystemExit('Setup stopped. No passwords or connection details are printed. Do not retry automatically.') from None
