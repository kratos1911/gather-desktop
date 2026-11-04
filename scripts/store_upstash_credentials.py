"""Hidden local token entry. No network calls, cloud changes or secret output."""
import argparse
import base64
from getpass import getpass
import secrets

from services.worker.local_query_cache import save, load, STORE


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--store',action='store_true')
    group.add_argument('--status',action='store_true')
    args=parser.parse_args()
    if args.status:
        value=load()
        print('Protected configuration available for Gather cache database '+value['database_id'])
        return
    if STORE.exists() or STORE.is_symlink():
        raise ValueError('existing_cache_credentials_preserved')
    print('Gather cache setup: the token and generated encryption key stay protected on D:.')
    print('Use the HTTPS REST URL and Token from your Upstash database. No network call is made here.')
    endpoint=input('Upstash REST URL: ').strip()
    token=getpass('Upstash REST Token (hidden): ')
    save(dict(version=1,endpoint=endpoint,token=token,
        key=base64.b64encode(secrets.token_bytes(32)).decode(),
        database_id='40316b37-032e-4eb6-984b-ae6ad3dfffe9'))
    print('Protected Gather cache configuration saved. No cloud changes were made.')


if __name__=='__main__':
    try:
        main()
    except (Exception,KeyboardInterrupt):
        raise SystemExit('Cache setup stopped. Existing files were preserved; no token was printed. Check input locally before retrying.') from None
