"""Cloud configuration/composition checks; no sockets, live Google or models."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from services.inference.asgi import create_app, create_server, LocalBearer, BoundedProtocol
from services.inference.cloud_startup import build_cloud_server, cloud_port, load_cloud_policy, main
from services.inference.startup import create_trusted_app, load_identity

AUDIENCE = 'https://gather-fixture.run.app'
EMAIL = 'gather-worker@sample-project.iam.gserviceaccount.com'


class CloudStartupTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.dumps({'audience': AUDIENCE, 'callers': [
            {'email': EMAIL, 'subject': '123456789'}]}).encode()
        self.identity = load_identity(self.raw)
        self.policy_value = {'audience': AUDIENCE,
            'invoker_members': ['serviceAccount:'+EMAIL], 'invoker_check_required': True}
        self.policy_raw = json.dumps(self.policy_value).encode()
        self.policy = load_cloud_policy(self.policy_raw, self.identity)
        self.runtime = MagicMock(request_timeout=15, ready=False)
        self.app = create_trusted_app(self.raw, self.runtime)

    def test_explicit_cloud_factory_reuses_bounded_server(self):
        with patch('services.inference.cloud_startup.build_verified_app', return_value=self.app) as build:
            server = build_cloud_server(self.raw, self.policy_raw, '/immutable/model', '8080')
        build.assert_called_once_with(self.raw, '/immutable/model')
        config = server.config
        self.assertEqual((config.host, config.port, config.workers), ('0.0.0.0', 8080, 1))
        self.assertIs(config.http, BoundedProtocol)
        self.assertFalse(config.proxy_headers)
        self.assertFalse(config.access_log)
        self.assertEqual(config.timeout_graceful_shutdown, 5)
        self.assertFalse(server.started)
        self.runtime.start.assert_not_called()

    def test_environment_cannot_enable_cloud_on_local_server(self):
        with patch.dict('os.environ', {'PORT': '9000', 'K_SERVICE': 'fixture'}):
            server = create_server(self.app)
        self.assertEqual((server.config.host, server.config.port), ('127.0.0.1', 8080))

    def test_unmanaged_auth_cannot_bind_publicly(self):
        for auth in (LocalBearer('x'*32), lambda headers: True):
            app = create_app(self.runtime, auth)
            with self.assertRaisesRegex(ValueError, 'cloud_identity_not_configured'):
                create_server(app, host='0.0.0.0', cloud_policy=self.policy)
        self.runtime.start.assert_not_called()

    def test_public_binding_requires_matching_policy(self):
        from services.worker.cloud_identity import IdentityConfig
        wrong = IdentityConfig('https://other.run.app', EMAIL, ('serviceAccount:'+EMAIL,))
        for host, policy in [('0.0.0.0', None), ('0.0.0.0', wrong), ('::', self.policy),
                             ('192.0.2.1', self.policy)]:
            with self.subTest(host=host), self.assertRaisesRegex(ValueError, 'cloud_identity_not_configured'):
                create_server(self.app, host=host, cloud_policy=policy)

    def test_policy_rejects_weak_or_mismatched_declarations(self):
        bad = [b'{}', b'x'*4097, b'{"audience":"a","audience":"b"}']
        for changes in ({'invoker_check_required': False}, {'invoker_check_required': 1},
                        {'invoker_members': ['allUsers']}, {'invoker_members': []},
                        {'invoker_members': self.policy_value['invoker_members']*2},
                        {'audience': 'https://other.run.app'}, {'unexpected': True},
                        {'invoker_members': ['serviceAccount:other-caller@sample-project.iam.gserviceaccount.com']}):
            bad.append(json.dumps(dict(self.policy_value, **changes)).encode())
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, 'invalid_cloud_policy'):
                load_cloud_policy(raw, self.identity)

    def test_two_callers_require_exact_invoker_set(self):
        identity = load_identity(json.dumps({'audience': AUDIENCE, 'callers': [
            {'email': EMAIL, 'subject': '123'},
            {'email': 'gather-api@sample-project.iam.gserviceaccount.com', 'subject': '456'}]}).encode())
        with self.assertRaises(ValueError):
            load_cloud_policy(self.policy_raw, identity)
        both = dict(self.policy_value, invoker_members=[
            'serviceAccount:gather-api@sample-project.iam.gserviceaccount.com', 'serviceAccount:'+EMAIL])
        self.assertEqual(len(load_cloud_policy(json.dumps(both).encode(), identity).invoker_members), 2)

    def test_invalid_configuration_never_reads_model_artifacts(self):
        with patch('services.inference.cloud_startup.build_verified_app') as build:
            for identity, policy, port in [(b'{}', self.policy_raw, '8080'),
                    (self.raw, b'{}', '8080'), (self.raw, self.policy_raw, None)]:
                with self.assertRaises(ValueError):
                    build_cloud_server(identity, policy, '/model', port)
            build.assert_not_called()

    def test_port_is_required_bounded_ascii_decimal(self):
        for value in (None, '', '0', '-1', '+8080', ' 8080', '8080\n', '65536',
                      '1e3', '８０８０', '999999', 8080):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'invalid_cloud_port'):
                cloud_port(value)
        for value in ('1', '8080', '65535'):
            self.assertEqual(cloud_port(value), int(value))
        for value in (0, True, 65536, '8080'):
            with self.assertRaisesRegex(ValueError, 'invalid_cloud_port'):
                create_server(self.app, host='0.0.0.0', port=value, cloud_policy=self.policy)

    def test_artifact_failure_never_constructs_server(self):
        with (patch('services.inference.cloud_startup.build_verified_app', side_effect=ValueError('bad artifacts')),
              patch('services.inference.asgi.create_server') as server):
            with self.assertRaises(ValueError):
                build_cloud_server(self.raw, self.policy_raw, '/model', '8080')
            server.assert_not_called()

    def test_cli_passes_only_explicit_files_and_platform_port(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]/'output') as folder:
            root = Path(folder)
            identity, policy = root/'identity.json', root/'policy.json'
            identity.write_bytes(self.raw)
            policy.write_bytes(self.policy_raw)
            argv = ['cloud_startup', '--identity', str(identity), '--deployment-policy',
                    str(policy), '--model', str(root/'model')]
            server = MagicMock(started=True)
            with (patch('sys.argv', argv), patch.dict('os.environ', {'PORT': '9090'}),
                  patch('services.inference.cloud_startup.build_cloud_server', return_value=server) as build):
                main()
                build.assert_called_once_with(self.raw, self.policy_raw, root/'model', '9090')
                server.run.assert_called_once()
                server.started = False
                with self.assertRaisesRegex(SystemExit, '^cloud_startup_failed$'):
                    main()
            identity.write_bytes(b'x'*5000)
            with (patch('sys.argv', argv),
                  patch('services.inference.cloud_startup.build_cloud_server', side_effect=ValueError('private detail')) as build):
                with self.assertRaisesRegex(SystemExit, '^cloud_startup_validation_failed$'):
                    main()
                self.assertEqual(len(build.call_args.args[0]), 4097)

    def test_cli_requires_policy(self):
        import contextlib
        import io
        with patch('sys.argv', ['cloud_startup', '--identity', 'unused', '--model', 'unused']):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)
