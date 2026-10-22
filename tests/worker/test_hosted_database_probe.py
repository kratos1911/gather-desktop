import unittest
from dataclasses import replace
from unittest.mock import patch, MagicMock

from scripts.check_hosted_database import check_role, ProbeError
from services.worker.database_transport import DatabaseConfig


class ProbeTests(unittest.TestCase):
    def test_pilot_probe_selects_ten_second_handshake(self):
        config = DatabaseConfig('127.0.0.1',5432,'gather_worker','fixture',test_loopback=True)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = ('gather_ingestion_worker',)
        with patch('services.worker.local_credentials.database_config',return_value=config), patch(
                'services.worker.database_transport.connect',return_value=connection) as connect:
            check_role('gather_worker',pilot_profile=True)
        self.assertEqual(connect.call_args.args[0],replace(config,connect_timeout=10))

    def test_authentication_error_is_redacted(self):
        error = RuntimeError('private password/details')
        error.pgcode = '28P01'
        with patch('services.worker.local_credentials.database_config'), patch(
                'services.worker.database_transport.connect',side_effect=error):
            with self.assertRaisesRegex(ProbeError,'^database_authentication_failed$'):
                check_role('gather_worker')

    def test_probe_rolls_back_and_closes_without_job_calls(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ('gather_ingestion_worker',)
        with patch('services.worker.local_credentials.database_config'), patch(
                'services.worker.database_transport.connect',return_value=connection):
            self.assertTrue(check_role('gather_worker')['connected'])
        cursor.execute.assert_called_once_with('select current_user')
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()


if __name__=='__main__':
    unittest.main()
