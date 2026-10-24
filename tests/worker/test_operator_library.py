import unittest
from unittest.mock import Mock, patch

from scripts.operator_library import PilotSession, PilotWorker, PILOT_USERS, main, RAW, QUERY
from services.worker.library_session import LibraryError
from services.worker.service_clients import SessionClient


class OperatorTests(unittest.TestCase):
    def test_worker_refuses_foreign_owner_and_nonfixture_original(self):
        repo = Mock()
        worker = PilotWorker(repo,'job')
        repo.call.return_value = {'id':'job','owner_id':'foreign'}
        with self.assertRaisesRegex(ValueError,'pilot_user_only'):
            worker.call('claim_text_job')
        repo.call.return_value = b'personal'.hex()
        with self.assertRaisesRegex(ValueError,'pilot_fixture_only'):
            worker.call('read_job_original','job','lease')
    def test_preview_has_no_secret_or_network_work(self):
        with patch('sys.argv',['operator_library']), patch('scripts.operator_library.google_token') as token, patch('scripts.operator_library.database_config') as config:
            main()
            token.assert_not_called()
            config.assert_not_called()

    def test_non_pilot_user_rejected_for_reads_and_search(self):
        api = Mock(spec=SessionClient,return_value={'id':'00000000-0000-0000-0000-000000000001'})
        provider = Mock()
        library = PilotSession(api,Mock(),provider)
        for action in (lambda:library.status('id'),lambda:library.search(QUERY)):
            with self.assertRaises(LibraryError): action()
        provider.infer.assert_not_called()
        self.assertTrue(all(c.args[1]=='/auth/v1/user' for c in api.call_args_list))

    def test_personal_content_and_arbitrary_queries_rejected(self):
        api = Mock(spec=SessionClient,return_value={'id':next(iter(PILOT_USERS))})
        factory,provider = Mock(),Mock()
        library = PilotSession(api,factory,provider)
        with self.assertRaises(LibraryError): library.import_text(original=b'personal',media='text/plain')
        with self.assertRaises(LibraryError): library.search('arbitrary query')
        factory.assert_not_called()
        provider.infer.assert_not_called()

    def test_fixed_fixture_reuses_existing_admission(self):
        api = Mock(spec=SessionClient,return_value={'id':next(iter(PILOT_USERS))})
        library = PilotSession(api,Mock(),Mock())
        with patch('services.worker.library_session.submit',return_value={'state':'queued'}) as submit:
            library.import_text(original=RAW,media='text/plain',request_id='id',title='Synthetic')
            self.assertEqual(submit.call_args.kwargs['original'],RAW)
