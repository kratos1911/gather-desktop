"""Configuration/transport checks only; no cloud deployment or model loads."""
import unittest
from unittest.mock import Mock,patch
from services.worker.cloud_library import configuration
from services.worker.library_server import create_cloud_server,create_server
from services.worker.library_api import LibraryAPI
from services.worker.service_clients import SessionClient
from services.worker.service_transport import TransportError
from tests.worker.test_service_clients import token


class CloudLibraryTests(unittest.TestCase):
    def test_wrong_service_or_missing_configuration_fails_before_secret_reads(self):
        for env in ({},{'K_SERVICE':'intrixshield','PORT':'8080'},
                    {'K_SERVICE':'gather-library-pilot','PORT':'8080','GATHER_PROJECT':'gather-development-511211'}):
            with patch('services.worker.cloud_library.Path') as path:
                with self.assertRaises(ValueError): configuration(env)
                path.assert_not_called()

    def test_cloud_bind_is_explicit_and_local_default_stays_loopback(self):
        app=LibraryAPI(Mock())
        with self.assertRaises(ValueError): create_cloud_server(app,{})
        self.assertEqual(create_server(app,port=0).config.host,'127.0.0.1')
        server=create_cloud_server(app,{'K_SERVICE':'gather-library-pilot','PORT':'8080'})
        self.assertEqual(server.config.host,'0.0.0.0')
        self.assertEqual(server.config.port,8080)
        self.assertEqual(app.cloud_origins,('http://tauri.localhost','tauri://localhost'))
        self.assertEqual(app.cloud_host,'gather-library-pilot-119730530113.asia-south1.run.app')

    def test_real_session_client_allows_only_scoped_recovery_and_cleanup_shapes(self):
        client=SessionClient('https://fixture.example','sb_publishable_fixture',token('authenticated'))
        routes=(('request_automatic_processing',{'p_source':'source','p_job':'job','p_attempts':1}),
                ('complete_source_cleanup',{'p_source':'source'}),('list_source_cleanup',{}))
        with patch('services.worker.service_clients.request_json',return_value=True) as send:
            for name,payload in routes:
                client('POST','/rest/v1/rpc/'+name,payload)
                with self.assertRaises(TransportError):client('POST','/rest/v1/rpc/'+name,dict(payload,owner='foreign'))
            self.assertEqual(send.call_count,3)
