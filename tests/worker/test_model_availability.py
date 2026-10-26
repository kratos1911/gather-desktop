"""Synthetic identity/HTTP/control checks. No cloud/model or document operations."""
import io
import json
import threading
import unittest
from email.message import Message
from urllib.error import HTTPError
from unittest.mock import Mock, patch

from scripts.check_cloud_ingestion import BoundedProvider
from scripts.operator_library import RefreshingPilotToken
from services.inference.runtime import InferenceError
from services.worker.cloud_identity import IdentityConfig
from services.worker.library_session import LibrarySession, LibraryError
from services.worker.model_availability import MODEL_HTTP, ModelServiceError
from services.worker.service_clients import CloudInferenceClient, SessionClient
from services.worker.service_transport import TransportError, inference_error_code

OWNER='00000000-0000-0000-0000-000000000001'
AUD='https://gather-test.run.app'
EMAIL='gather-test@sample-project.iam.gserviceaccount.com'


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.cancel=threading.Event()
        config=IdentityConfig(AUD,EMAIL,('serviceAccount:'+EMAIL,))
        self.identity=Mock(config=config)
        self.identity.get.return_value='synthetic-service-token'
        self.count=Mock(return_value=1)
        self.client=CloudInferenceClient(config,self.count,token_provider=self.identity)

    def test_readiness_is_one_fixed_authenticated_get_without_tokenizing(self):
        with patch('services.worker.service_clients.request_json',return_value={'ready':True}) as send:
            self.assertEqual(self.client.check_ready(cancel=self.cancel),'ready')
        self.assertEqual(send.call_count,1)
        self.assertEqual(send.call_args.args[:2],(AUD,'/ready'))
        self.assertIsNone(send.call_args.args[3])
        self.assertEqual(send.call_args.args[2],{'Authorization':'Bearer synthetic-service-token',
            'X-Serverless-Authorization':'Bearer synthetic-service-token'})
        self.assertLessEqual(send.call_args.kwargs['timeout'],15)
        self.identity.get.assert_called_once_with(cancel=self.cancel,timeout=5)
        self.count.assert_not_called()

    def test_identity_failure_does_not_send_and_operator_token_respects_allowance(self):
        self.identity.get.side_effect=RuntimeError('private credential details')
        with patch('services.worker.service_clients.request_json') as send:
            self.assertEqual(self.client.check_ready(cancel=self.cancel),'model_identity_unavailable')
        send.assert_not_called()
        with patch('scripts.operator_library.google_token') as mint:
            RefreshingPilotToken().get(cancel=self.cancel,timeout=2)
            mint.assert_called_once_with(timeout=2)

    def test_transport_reasons_and_inference_compatibility_without_retry(self):
        cases={'authentication_failed':'model_access_denied','rate_limited':'model_rate_limited',
            'model_busy':'model_busy','busy':'model_busy','timeout':'model_deadline',
            'model_not_ready':'model_not_ready','inference_deadline':'model_deadline',
            'service_unavailable':'model_unavailable'}
        for transport,expected in cases.items():
            with self.subTest(code=transport),patch('services.worker.service_clients.request_json',side_effect=TransportError(transport)) as send:
                self.assertEqual(self.client.check_ready(cancel=self.cancel),expected)
                self.assertEqual(send.call_count,1)
                with self.assertRaises(ModelServiceError) as error:
                    self.client.infer({'role':'query','texts':['fixture']},cancel=self.cancel)
                self.assertEqual(error.exception.reason,expected)
                self.assertEqual(send.call_count,2)  # Two explicit operations, no retry.
        self.assertGreaterEqual(self.identity.invalidate.call_count,2)

    def test_readiness_is_not_a_promise_and_unknown_output_is_redacted(self):
        for value,expected in (({'ready':False},'model_not_ready'),
                              ({'ready':True,'token':'private'},'model_unavailable'),
                              ({'ready':1},'model_unavailable')):
            with patch('services.worker.service_clients.request_json',return_value=value):
                self.assertEqual(self.client.check_ready(cancel=self.cancel),expected)

    def test_cancelled_probe_does_not_fetch_identity(self):
        self.cancel.set()
        with self.assertRaisesRegex(InferenceError,'^cancelled$'):
            self.client.check_ready(cancel=self.cancel)
        self.identity.get.assert_not_called()

    def test_budget_is_unchanged_and_checks_do_not_reset_or_consume_it(self):
        provider=Mock()
        provider.check_ready.return_value='ready'
        bounded=BoundedProvider(provider)
        self.assertEqual(bounded.check_ready(cancel=self.cancel),{'state':'ready','used':0,'limit':3})
        for _ in range(3): bounded.infer({'role':'query','texts':['fixture']},cancel=self.cancel)
        with self.assertRaises(ModelServiceError) as error:
            bounded.infer({},cancel=self.cancel)
        self.assertEqual(error.exception.reason,'model_budget_exhausted')
        self.assertEqual(provider.infer.call_count,3)
        self.assertEqual(bounded.check_ready(cancel=self.cancel),{'state':'model_budget_exhausted','used':3,'limit':3})
        self.assertEqual(provider.check_ready.call_count,1)

    def test_session_auth_before_probe_and_strict_output(self):
        api=Mock(spec=SessionClient,return_value={'id':OWNER})
        provider=Mock()
        provider.check_ready.return_value={'state':'ready','used':0,'limit':3}
        session=LibrarySession(api,Mock(),provider)
        self.assertEqual(session.model_status(cancel=self.cancel)['state'],'ready')
        self.assertEqual(api.call_count,1)
        self.assertEqual(api.call_args.args,('GET','/auth/v1/user'))
        provider.check_ready.assert_called_once_with(cancel=self.cancel)
        provider.check_ready.reset_mock()
        api.side_effect=ValueError('private auth details')
        with self.assertRaisesRegex(LibraryError,'^session_unavailable$'): session.model_status(cancel=self.cancel)
        provider.check_ready.assert_not_called()
        api.side_effect=None
        provider.check_ready.return_value={'state':'ready','used':0,'limit':3,'secret':'private'}
        with self.assertRaisesRegex(LibraryError,'^model_unavailable$'): session.model_status(cancel=self.cancel)

    def test_only_small_exact_inference_error_shapes_are_recognized(self):
        def error(code,body,content_type='application/json'):
            headers=Message(); headers['Content-Type']=content_type
            return HTTPError(AUD+'/embed',code,'fixture',headers,io.BytesIO(body))
        for code,body,expected in ((429,b'{"error":"busy"}',b'model_busy'),
            (503,b'{"error":"model_unavailable"}',b'model_not_ready'),
            (504,b'{"error":"deadline_exceeded"}',b'inference_deadline'),
            (429,b'{"error":"private upstream details"}',None),
            (429,b'{"error":"busy","secret":"private"}',None),
            (429,b'x'*4097,None)):
            self.assertEqual(inference_error_code(AUD+'/embed',error(code,body)),expected)
        self.assertIsNone(inference_error_code(AUD+'/other',error(429,b'{"error":"busy"}')))
        self.assertEqual(inference_error_code(AUD+'/ready',error(503,b'{"ready":false}')),b'model_not_ready')
