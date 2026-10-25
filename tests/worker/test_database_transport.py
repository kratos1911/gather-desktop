import json
import io
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import Mock, patch, MagicMock

from services.worker.database_transport import DatabaseConfig, DatabaseRepository, connect, encode_result, child_main
from services.worker.ingestion_repository import RepositoryError

OWNER = '00000000-0000-0000-0000-000000000001'


class DatabaseTransportTests(unittest.TestCase):
    def test_targeted_claim_is_worker_only_and_preserves_job_parameter(self):
        child = Mock(returncode=0)
        child.poll.return_value = 0
        child.communicate.return_value = (b'{"result":null}',None)
        with patch('services.worker.database_transport.subprocess.Popen',return_value=child):
            self.assertIsNone(DatabaseRepository(self.config()).call('claim_target_text_job',OWNER))
        wire = json.loads(child.communicate.call_args_list[0].kwargs['input'])
        self.assertEqual((wire['function'],wire['args']),('claim_target_text_job',[OWNER]))
        with patch('services.worker.database_transport.subprocess.Popen') as spawn:
            with self.assertRaises(ValueError):
                DatabaseRepository(self.config(user='gather_admission'),owner=OWNER).call('claim_target_text_job',OWNER)
            spawn.assert_not_called()

    def test_child_accepts_explicit_pilot_profile_with_same_total(self):
        config = self.config(connect_timeout=10)
        wire = dict(config=asdict(config),owner=None,function='claim_text_job',args=[],operation_timeout=15)
        output = io.BytesIO()
        with patch('services.worker.database_transport.sys.stdin',Mock(buffer=io.BytesIO(json.dumps(wire).encode()))), patch(
                'services.worker.database_transport.sys.stdout',Mock(buffer=output)), patch(
                'services.worker.database_transport.PostgresRepository') as repository:
            repository.return_value.call.return_value = None
            child_main()
        self.assertEqual(json.loads(output.getvalue()),{'result':None})
        repository.return_value.call.assert_called_once_with('claim_text_job')

    def test_longer_handshake_requires_explicit_pilot_total(self):
        config = self.config(connect_timeout=10)
        with self.assertRaises(ValueError):
            DatabaseRepository(config)
        self.assertEqual(DatabaseRepository(config,operation_timeout=15).operation_timeout,15)
        for invalid in (0,5,11,True,'10'):
            with self.assertRaises(ValueError):
                self.config(connect_timeout=invalid)

    def test_pilot_handshake_reaches_driver_and_child_wire(self):
        config = self.config(connect_timeout=10)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (False,)*5
        with patch('psycopg2.connect',return_value=connection) as driver:
            connect(config,None)
        self.assertEqual(driver.call_args.kwargs['connect_timeout'],10)
        child = Mock(returncode=0)
        child.poll.return_value = 0
        child.communicate.return_value = (b'{"result":null}',None)
        with patch('services.worker.database_transport.subprocess.Popen',return_value=child):
            DatabaseRepository(config,operation_timeout=15).call('claim_text_job')
        value = json.loads(child.communicate.call_args_list[0].kwargs['input'])
        self.assertEqual(value['operation_timeout'],15)
        self.assertEqual(value['config']['connect_timeout'],10)

    def test_production_default_and_explicit_pilot_bounds(self):
        default = DatabaseRepository(self.config())
        pilot = DatabaseRepository(self.config(),operation_timeout=15)
        self.assertEqual((default.operation_timeout,default.cleanup_wait_seconds),(5,6))
        self.assertEqual((pilot.operation_timeout,pilot.cleanup_wait_seconds),(15,16))
        for invalid in (0,10,16,True,'15',15.0):
            with self.assertRaises(ValueError):
                DatabaseRepository(self.config(),operation_timeout=invalid)

    def test_lease_timestamp_result_preserves_timezone(self):
        value = datetime(2026,10,21,tzinfo=timezone.utc)
        self.assertEqual(json.loads(json.dumps({'result':value},default=encode_result)),
                         {'result':'2026-10-21T00:00:00+00:00'})
        with self.assertRaises(TypeError):
            encode_result(datetime(2026,10,21))

    def config(self, **overrides):
        return DatabaseConfig(**(dict(host='127.0.0.1',port=5432,user='gather_worker',
                                     password='synthetic-secret',test_loopback=True)|overrides))

    def test_config_rejects_dsn_injection_and_unsafe_roles(self):
        for values in (dict(host='host,password=bad'),dict(user='postgres'),dict(port=True),
                       dict(test_loopback=True,host='remote.example'),dict(test_loopback=False),dict(password='')):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.config(**values)
        self.assertNotIn('synthetic-secret',repr(self.config()))

    def test_roles_and_operations_are_separate(self):
        with self.assertRaises(ValueError):
            DatabaseRepository(self.config(),owner=OWNER)
        with self.assertRaises(ValueError):
            DatabaseRepository(self.config(user='gather_admission'))
        repo = DatabaseRepository(self.config())
        with patch('services.worker.database_transport.subprocess.Popen') as process:
            for function in ('submit_text','unsafe;sql'):
                with self.assertRaises(ValueError):
                    repo.call(function)
            process.assert_not_called()

    def test_secrets_only_in_stdin_and_no_environment_credentials(self):
        child = Mock(returncode=0)
        child.communicate.return_value = (b'{"result":null}',None)
        child.poll.return_value = 0
        with patch('services.worker.database_transport.subprocess.Popen',return_value=child) as start:
            self.assertIsNone(DatabaseRepository(self.config()).call('claim_text_job'))
        self.assertNotIn('synthetic-secret',repr(start.call_args))
        wire = child.communicate.call_args_list[0].kwargs['input']
        self.assertEqual(json.loads(wire)['config']['password'],'synthetic-secret')
        self.assertNotIn('PGPASSWORD',start.call_args.kwargs['env'])

    def test_whole_deadline_reaps_actual_stalled_child(self):
        real_start = subprocess.Popen
        processes = []
        def stalled(*args, **kwargs):
            process = real_start([sys.executable,'-I','-c','import time; time.sleep(30)'],**kwargs)
            processes.append(process)
            return process
        started = time.monotonic()
        repository = DatabaseRepository(self.config())
        with patch('services.worker.database_transport.subprocess.Popen',side_effect=stalled), patch.object(
                repository,'operation_timeout',.15):
            with self.assertRaisesRegex(RepositoryError,'^temporarily_unavailable$'):
                repository.call('claim_text_job')
        self.assertLess(time.monotonic()-started,3)
        self.assertIsNotNone(processes[0].poll())

    def test_tls_owner_context_and_fixed_role(self):
        config = self.config(host='db.example.supabase.co',user='gather_admission',test_loopback=False,
                             root_certificate=str(Path(__file__).resolve()))
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (False,)*5
        with patch('psycopg2.connect',return_value=connection) as driver:
            self.assertIs(connect(config,OWNER),connection)
        self.assertEqual(driver.call_args.kwargs['sslmode'],'verify-full')
        self.assertEqual(driver.call_args.kwargs['connect_timeout'],3)
        self.assertIn('statement_timeout=5000',driver.call_args.kwargs['options'])
        self.assertEqual(cursor.execute.call_args.args,
            ("select pg_catalog.set_config('request.jwt.claim.sub',%s,true)",(OWNER,)))
        self.assertIn(('set local role gather_ingestion_coordinator',),
                      [call.args for call in cursor.execute.call_args_list])

    def test_privileged_login_closes_before_operation(self):
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (True,False,False,False,False)
        with patch('psycopg2.connect',return_value=connection):
            with self.assertRaises(ValueError):
                connect(self.config(),None)
        connection.close.assert_called_once()

    def test_malformed_output_is_safe_and_releases_capacity(self):
        child = Mock(returncode=0)
        child.poll.return_value = 0
        child.communicate.return_value = (b'private driver details',None)
        with patch('services.worker.database_transport.subprocess.Popen',return_value=child):
            for _ in range(3):
                with self.assertRaisesRegex(RepositoryError,'^temporarily_unavailable$'):
                    DatabaseRepository(self.config()).call('claim_text_job')


if __name__=='__main__':
    unittest.main()
