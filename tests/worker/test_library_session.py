import unittest
from unittest.mock import Mock, patch

from services.worker.library_session import LibrarySession, LibraryError
from services.worker.search import SearchError
from services.worker.service_clients import SessionClient

OWNER = '00000000-0000-0000-0000-000000000001'
SOURCE = '00000000-0000-0000-0000-000000000002'


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.api = Mock(spec=SessionClient, return_value={'id':OWNER})
        self.factory, self.provider = Mock(), Mock()
        self.session = LibrarySession(self.api, self.factory, self.provider)

    def test_invalid_session_prevents_admission_and_inference(self):
        self.api.side_effect = RuntimeError('private credential details')
        with self.assertRaisesRegex(LibraryError, '^session_unavailable$'):
            self.session.import_text(request_id=SOURCE,title='test',original=b'x',media='text/plain')
        with self.assertRaisesRegex(LibraryError, '^session_unavailable$'):
            self.session.search('query')
        self.factory.assert_not_called()
        self.provider.infer.assert_not_called()

    def test_search_preserves_only_allowlisted_dependency_diagnostic(self):
        for code in ('session_unavailable','model_unavailable','library_unavailable','search_failed'):
            with patch('services.worker.library_session.search',side_effect=SearchError(code)):
                with self.assertRaisesRegex(LibraryError,'^'+code+'$'):
                    self.session.search('query')
        with patch('services.worker.library_session.search',side_effect=SearchError('secret document text')):
            with self.assertRaisesRegex(LibraryError,'^search_failed$'):
                self.session.search('query')

    def test_import_owner_comes_from_auth_not_payload(self):
        with patch('services.worker.library_session.submit', return_value={'queued':True}) as submit:
            self.session.import_text(request_id=SOURCE,title='test',original=b'x',media='text/plain')
            self.factory.assert_called_once_with(OWNER)
            self.assertNotIn('owner', submit.call_args.kwargs)
        with self.assertRaises(TypeError):
            self.session.import_text(owner=SOURCE)

    def test_every_operation_rechecks_auth_and_retains_session(self):
        self.session.status(SOURCE)
        self.session.open(SOURCE, OWNER)
        self.session.delete(SOURCE)
        self.assertEqual([call.args[1] for call in self.api.call_args_list], [
            '/auth/v1/user','/rest/v1/rpc/source_processing_status_with_recovery',
            '/auth/v1/user','/rest/v1/rpc/open_published_text',
            '/auth/v1/user','/rest/v1/rpc/request_source_deletion'])
        self.factory.assert_not_called()
        self.provider.infer.assert_not_called()

    def test_malformed_auth_identity_never_reaches_admission(self):
        self.api.return_value = {'id':'invalid'}
        with self.assertRaises(LibraryError):
            self.session.import_text(request_id=SOURCE,title='test',original=b'x',media='text/plain')
        self.factory.assert_not_called()

    def test_invalid_resource_identifier_does_not_reach_rpc(self):
        with self.assertRaisesRegex(LibraryError, '^library_operation_failed$'):
            self.session.delete("'; drop table sources")
        self.assertEqual(self.api.call_count, 1)

    def test_database_failure_is_redacted(self):
        self.factory.side_effect = RuntimeError('secret connection details')
        with self.assertRaisesRegex(LibraryError, '^import_failed$'):
            self.session.import_text(request_id=SOURCE,title='test',original=b'x',media='text/plain')


if __name__ == '__main__':
    unittest.main()
