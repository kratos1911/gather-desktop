import unittest
import io
import json
from contextlib import redirect_stdout
from unittest.mock import Mock, MagicMock, patch
from scripts.set_supabase_passwords import validate_passwords, verify_role, ROLES, child, main


class PasswordSetupTests(unittest.TestCase):
    def test_short_password_reports_role_without_starting_child(self):
        with patch('sys.argv',['setup','--apply']), patch('scripts.set_supabase_passwords.CERT') as cert, patch(
                'scripts.set_supabase_passwords.getpass.getpass',side_effect=['admin','short','short','b'*24,'b'*24]), patch(
                'scripts.set_supabase_passwords.subprocess.run') as run, redirect_stdout(io.StringIO()):
            cert.is_file.return_value = True
            with self.assertRaisesRegex(SystemExit,'gather_admission password must contain at least 24 characters'):
                main()
            run.assert_not_called()

    def test_check_input_never_starts_database_child(self):
        with patch('sys.argv',['setup','--check-input']), patch('scripts.set_supabase_passwords.CERT') as cert, patch(
                'scripts.set_supabase_passwords.getpass.getpass',side_effect=['admin','a'*24,'a'*24,'b'*24,'b'*24]), patch(
                'scripts.set_supabase_passwords.subprocess.run') as run, redirect_stdout(io.StringIO()):
            cert.is_file.return_value = True
            main()
            run.assert_not_called()

    def test_commit_failure_reports_unknown_outcome(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (True,False,False,False,False,False,False)
        cursor.fetchall.side_effect = [[(role,)] for role in ROLES.values()]
        connection.__exit__.side_effect = RuntimeError('connection lost during commit')
        values = {'postgres':'existing-admin','gather_admission':'a'*24,'gather_worker':'b'*24}
        output = io.StringIO()
        with patch('scripts.set_supabase_passwords.connect',return_value=connection), patch(
                'scripts.set_supabase_passwords.sys.stdin',Mock(buffer=io.BytesIO(json.dumps(values).encode()))), patch(
                'psycopg2.extensions.encrypt_password',return_value='synthetic-verifier'), redirect_stdout(output):
            with self.assertRaises(SystemExit):
                child()
        self.assertIsNone(json.loads(output.getvalue())['passwords_committed'])

    def test_preflight_failure_does_not_change_passwords(self):
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = None
        values = {'postgres':'existing-admin','gather_admission':'a'*24,'gather_worker':'b'*24}
        stdin = Mock(buffer=io.BytesIO(json.dumps(values).encode()))
        output = io.StringIO()
        with patch('scripts.set_supabase_passwords.connect',return_value=connection), patch(
                'scripts.set_supabase_passwords.sys.stdin',stdin), patch(
                'psycopg2.extensions.encrypt_password') as encrypt, redirect_stdout(output):
            with self.assertRaises(SystemExit):
                child()
            encrypt.assert_not_called()
        self.assertFalse(json.loads(output.getvalue())['passwords_committed'])
        connection.close.assert_called_once()

    def test_password_verifiers_only_and_both_logins_checked(self):
        connections = [MagicMock() for _ in range(3)]
        attributes = (True,False,False,False,False,False,False)
        admin = connections[0].cursor.return_value.__enter__.return_value
        admin.fetchone.return_value = attributes
        admin.fetchall.side_effect = [[(role,)] for role in ROLES.values()]
        for connection,target in zip(connections[1:],ROLES.values()):
            cursor = connection.cursor.return_value.__enter__.return_value
            cursor.fetchone.side_effect = [attributes,(target,)]
            cursor.fetchall.return_value = [(target,)]
        values = {'postgres':'existing-admin','gather_admission':'a'*24,'gather_worker':'b'*24}
        output = io.StringIO()
        with patch('scripts.set_supabase_passwords.connect',side_effect=connections) as connect, patch(
                'scripts.set_supabase_passwords.sys.stdin',Mock(buffer=io.BytesIO(json.dumps(values).encode()))), patch(
                'psycopg2.extensions.encrypt_password',return_value='synthetic-verifier'), redirect_stdout(output):
            child()
        self.assertEqual(connect.call_count,3)
        self.assertTrue(json.loads(output.getvalue())['success'])
        self.assertNotIn('a'*24,repr(admin.execute.call_args_list))
        self.assertNotIn('b'*24,repr(admin.execute.call_args_list))
        for connection in connections:
            connection.close.assert_called_once()

    def test_distinct_bounded_passwords_required(self):
        good = {'postgres':'existing-admin','gather_admission':'a'*24,'gather_worker':'b'*24}
        validate_passwords(good)
        for change in ({'gather_worker':'a'*24},{'gather_worker':'short'},{'gather_worker':'x\x00'*24}):
            with self.assertRaises(ValueError):
                validate_passwords(good|change)

    def test_privilege_check_precedes_membership(self):
        cursor = Mock()
        cursor.fetchone.return_value = (True,False,True,False,False,False,False)
        with self.assertRaises(ValueError):
            verify_role(cursor,'gather_worker')
        cursor.fetchall.assert_not_called()

    def test_exact_membership_required(self):
        cursor = Mock()
        cursor.fetchone.return_value = (True,False,False,False,False,False,False)
        for members in ([],[('postgres',)],[(ROLES['gather_worker'],),('service_role',)]):
            cursor.fetchall.return_value = members
            with self.assertRaises(ValueError):
                verify_role(cursor,'gather_worker')
        cursor.fetchall.return_value = [(ROLES['gather_worker'],)]
        verify_role(cursor,'gather_worker')


if __name__=='__main__':
    unittest.main()
