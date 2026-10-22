"""Save existing backend passwords encrypted for this Windows user. No network."""
import argparse
import getpass
import warnings

from services.worker.local_credentials import ROLES, STORE, save, load, CredentialError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--save',action='store_true')
    group.add_argument('--check',action='store_true')
    args = parser.parse_args()
    if args.check:
        load()
        print('Local decryption verified for both backend roles. No database connection made.')
        return
    if not args.save:
        print('Preview only. Encrypted destination: '+str(STORE))
        return
    if STORE.exists():
        raise CredentialError('credential_file_already_exists')
    warnings.simplefilter('error',getpass.GetPassWarning)
    values = {}
    try:
        for role in ROLES:
            password = getpass.getpass('Existing '+role+' password (hidden): ')
            if password != getpass.getpass('Confirm '+role+' password (hidden): '):
                raise CredentialError('password_confirmation_mismatch')
            values[role] = password
        save(values)
        load()
        print('Saved encrypted credentials; local decryption verified. No database changes made.')
    finally:
        values.clear()


if __name__=='__main__':
    try:
        main()
    except CredentialError as error:
        raise SystemExit(str(error)) from None
    except (Exception,KeyboardInterrupt):
        raise SystemExit('Credential setup stopped. No passwords are printed.') from None
