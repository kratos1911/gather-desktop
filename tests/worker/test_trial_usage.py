import threading
import unittest
from unittest.mock import Mock, patch

from scripts.operator_library import PILOT_USERS, PilotSession, PilotWorker
from services.worker.automatic_processing import AutomaticAdmission
from services.worker.library_session import LibraryError
from services.worker.model_availability import ModelServiceError, status_reply
from services.worker.trial_usage import TrialModel
from tests.worker.test_search import Provider, Session
from tests.worker.test_search_auth import client


class TrialUsageTests(unittest.TestCase):
    def test_search_reserves_using_verified_owner_and_cache_hit_does_not_charge(self):
        owner = sorted(PILOT_USERS)[0]
        data = Session()
        model = Provider()
        repo = Mock()
        repo.call.return_value = {'state':'available', 'used':12, 'limit':20}
        admission = Mock(return_value=AutomaticAdmission(repo))
        cache = Mock()
        cache.get.side_effect = [None, [1.]+[0.]*511, None]
        session = PilotSession(client(owner), admission, TrialModel(model),
                               text_files=True, query_cache=cache)

        def remote(base, path, headers, payload, **options):
            if path == '/auth/v1/user':
                return {'id':owner}
            return data('POST',path,payload)

        with patch('services.worker.service_clients.request_json', side_effect=remote):
            self.assertEqual(len(session.search('first query')['windows']), 1)
            self.assertEqual(len(session.search('first query')['windows']), 1)
            repo.call.assert_called_once_with('trial_query_usage', True)
            self.assertTrue(all(call.args == (owner,) for call in admission.call_args_list))
            self.assertEqual(len(model.calls), 1)
            repo.call.return_value = {'state':'trial_quota_exhausted', 'used':20, 'limit':20}
            with self.assertRaisesRegex(LibraryError, '^trial_quota_exhausted$'):
                session.search('second query')
            self.assertEqual(len(model.calls), 1)

    def test_document_reservation_requires_exact_claimed_job_and_lease(self):
        repository = Mock(cleanup_wait_seconds=6)
        worker = PilotWorker(repository, 'job', automatic=True)
        bound = TrialModel(Mock()).bind(worker.charge_trial_document)
        event = threading.Event()
        with self.assertRaisesRegex(ModelServiceError, '^service_unavailable$'):
            bound.infer({}, cancel=event)
        repository.call.assert_not_called()
        repository.call.side_effect = [
            {'id':'job', 'owner_id':sorted(PILOT_USERS)[0], 'lease_token':'lease'},
            {'state':'trial_capacity_exhausted', 'used':3, 'limit':20},
        ]
        worker.call('claim_text_job')
        with self.assertRaises(ModelServiceError) as exhausted:
            bound.infer({}, cancel=event)
        self.assertEqual(exhausted.exception.reason, 'trial_capacity_exhausted')
        repository.call.assert_called_with('charge_trial_document', 'job', 'lease')

    def test_uncertain_reservation_never_sends_or_retries(self):
        provider = Mock()
        reserve = Mock(side_effect=TimeoutError('private detail'))
        model = TrialModel(provider).bind(reserve)
        with self.assertRaises(ModelServiceError) as caught:
            model.infer({}, cancel=threading.Event())
        self.assertEqual(caught.exception.reason, 'model_unavailable')
        reserve.assert_called_once_with()
        provider.infer.assert_not_called()

    def test_allowance_check_is_read_only_and_skips_probe_when_exhausted(self):
        owner = sorted(PILOT_USERS)[0]
        provider = Mock()
        repo = Mock()
        repo.call.return_value = {'state':'trial_capacity_exhausted', 'used':3, 'limit':20}
        admission = Mock(return_value=AutomaticAdmission(repo))
        session = PilotSession(client(owner), admission, TrialModel(provider), text_files=True)
        with patch('services.worker.service_clients.request_json', return_value={'id':owner}):
            result = session.model_status(cancel=threading.Event())
        self.assertEqual(result, dict(repo.call.return_value, period='utc_day'))
        repo.call.assert_called_once_with('trial_query_usage', False)
        admission.assert_called_once_with(owner)
        provider.check_ready.assert_not_called()
        with self.assertRaises(ValueError):
            status_reply(dict(result, used=20))
