"""Real RSA verification with ephemeral synthetic keys; no Google calls."""
import base64
import json
import time
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from services.inference.service_auth import GoogleServiceAuth
from services.worker.cloud_identity import IdentityConfig

AUD = 'https://gather-model-example.run.app'
EMAIL = 'gather-api@sample-project.iam.gserviceaccount.com'
SUB = '123456789012345678901'


class ServiceAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.pem = cls.key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    def setUp(self):
        self.identity = IdentityConfig(AUD, EMAIL, ('serviceAccount:'+EMAIL,))
        self.auth = GoogleServiceAuth(self.identity, SUB, {'fixture':self.pem}, key_ttl=60)

    def token(self, changes=None, header=None, key=None, raw_claims=None):
        now = int(time.time())
        claims = dict(iss='https://accounts.google.com', aud=AUD, sub=SUB,
                      email=EMAIL, email_verified=True, iat=now-1, exp=now+3599)
        claims.update(changes or {})
        def enc(raw):
            return base64.urlsafe_b64encode(raw).rstrip(b'=')
        body = enc(json.dumps(header or dict(alg='RS256', kid='fixture', typ='JWT')).encode())
        body += b'.'+enc(raw_claims or json.dumps(claims).encode())
        signature = (key or self.key).sign(body, padding.PKCS1v15(), hashes.SHA256())
        return body+b'.'+enc(signature)

    def accepted(self, token):
        return self.auth([(b'authorization', b'Bearer '+token)])

    def test_valid_signature_and_pinned_identity(self):
        self.assertTrue(self.accepted(self.token()))
        self.assertTrue(self.accepted(self.token({'iss':'accounts.google.com'})))

    def test_client_handoff_keeps_application_signature_required(self):
        from services.worker.service_clients import CloudInferenceClient
        client = CloudInferenceClient(self.identity, lambda text: 1)
        token = self.token().decode('ascii')
        captured = []
        def platform_fixture(base, path, headers, body, **kwargs):
            self.assertEqual(headers['X-Serverless-Authorization'], 'Bearer '+token)
            self.assertEqual(headers['Authorization'], 'Bearer '+token)
            # Model the documented platform handoff, not actual Google IAM.
            forwarded = [(b'authorization', headers['Authorization'].encode()),
                         (b'x-serverless-authorization', b'Bearer stripped.fixture.')]
            self.assertTrue(self.auth(forwarded))
            self.assertFalse(self.auth(forwarded[1:]))
            self.assertFalse(self.auth([(b'authorization', b'Bearer stripped.fixture.'),
                                       forwarded[1]]))
            self.assertFalse(self.auth([forwarded[0], forwarded[0], forwarded[1]]))
            captured.append(True)
            return {'fixture': True}
        with patch.object(client._identity, 'get', return_value=token), patch(
                'services.worker.service_clients.request_json', side_effect=platform_fixture):
            self.assertEqual(client.infer({'role':'query','texts':['fixture']}, cancel=None),
                             {'fixture': True})
        self.assertEqual(captured, [True])

    def test_untrusted_signer_and_tampering(self):
        self.assertFalse(self.accepted(self.token(key=self.other)))
        token = self.token()
        parts = token.split(b'.')
        signature = bytearray(base64.urlsafe_b64decode(parts[2]+b'='*((-len(parts[2]))%4)))
        signature[0] ^= 1
        parts[2] = base64.urlsafe_b64encode(signature).rstrip(b'=')
        self.assertFalse(self.accepted(b'.'.join(parts)))

    def test_signed_but_unauthorized_claims(self):
        now = int(time.time())
        cases = [dict(aud='https://other.run.app'), dict(aud=[AUD]), dict(iss='attacker'),
                 dict(sub='987'), dict(email='other@sample-project.iam.gserviceaccount.com'),
                 dict(email_verified=False), dict(email_verified='true'), dict(exp=now-1),
                 dict(iat=now+100), dict(iat=True), dict(exp='9999999999'),
                 dict(exp=now+7200), dict(nbf=now+100), dict(nbf=False)]
        for changes in cases:
            with self.subTest(changes=changes):
                self.assertFalse(self.accepted(self.token(changes)))

    def test_algorithm_key_and_remote_key_header_rejection(self):
        for fields in [dict(alg='none'), dict(alg='HS256'), dict(kid='unknown'),
                       dict(jku='https://attacker.invalid/keys'), dict(jwk={}),
                       dict(crit=['custom']), dict(typ='other')]:
            with self.subTest(fields=fields):
                header = dict(alg='RS256',kid='fixture',typ='JWT') | fields
                self.assertFalse(self.accepted(self.token(header=header)))

    def test_bad_framing_and_duplicate_json(self):
        value = b'Bearer '+self.token()
        self.assertFalse(self.auth([]))
        self.assertFalse(self.auth([(b'authorization',value)]*2))
        self.assertFalse(self.auth([(b'authorization',value+b' ')]))
        for token in [b'a.b.c', b'x'*8193, b'\xff', self.token(raw_claims=b'{"aud":"a","aud":"b"}')]:
            self.assertFalse(self.accepted(token))

    def test_expired_snapshot_and_monotonic_clock(self):
        token = self.token()
        with patch('services.inference.service_auth.time.monotonic', return_value=self.auth._deadline):
            self.assertFalse(self.auth.ready)
            self.assertFalse(self.accepted(token))
        with patch('services.inference.service_auth.time.time', return_value=self.auth._expires):
            self.assertFalse(self.auth.ready)

    def test_snapshot_copied_and_invalid_config(self):
        keys = {'fixture':self.pem}
        auth = GoogleServiceAuth(self.identity, SUB, keys, key_ttl=60)
        keys.clear()
        self.assertTrue(auth([(b'authorization',b'Bearer '+self.token())]))
        for ttl in [0,301,True,float('nan')]:
            with self.assertRaises(ValueError):
                GoogleServiceAuth(self.identity, SUB, {'fixture':self.pem}, key_ttl=ttl)
        for keys in [{}, {'fixture':'invalid'}, {'fixture':self.pem} | {str(i):self.pem for i in range(8)}]:
            with self.assertRaises(ValueError):
                GoogleServiceAuth(self.identity, SUB, keys, key_ttl=60)

    def test_asgi_verifier_rejects_before_inference_and_expires_readiness(self):
        from tests.inference import test_asgi as harness
        rig = harness.ASGITests()
        with patch.object(harness, 'LocalBearer', return_value=self.auth):
            rig.setUp()
        try:
            with patch.object(rig.runtime, 'infer', wraps=rig.runtime.infer) as infer:
                self.assertEqual(rig.request(token=self.token(key=self.other).decode())[0],401)
                self.assertEqual(rig.request(token=self.token({'sub':'987'}).decode())[0],401)
                infer.assert_not_called()
                self.assertEqual(rig.request(token=self.token().decode())[0],200)
                self.assertEqual(infer.call_count,1)
                self.auth._deadline = 0
                self.assertEqual(rig.request(path='/ready'),(503,{'ready':False}))
                self.assertEqual(rig.request(token=self.token().decode())[0],401)
                self.assertEqual(infer.call_count,1)
            with self.assertRaisesRegex(ValueError, 'cloud_identity_not_configured'):
                harness.create_server(rig.app, host='0.0.0.0')
        finally:
            rig.tearDown()


if __name__ == '__main__':
    unittest.main()
