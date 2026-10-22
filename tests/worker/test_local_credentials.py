import json
import unittest
from unittest.mock import patch, Mock, MagicMock

from services.worker import local_credentials as store


class CredentialTests(unittest.TestCase):
    def test_invalid_input_never_reaches_encryption(self):
        with patch.object(store,'dpapi') as encrypt:
            for values in ({},{'gather_admission':'short','gather_worker':'b'*24},
                           dict.fromkeys(store.ROLES,'a'*24)):
                with self.assertRaises(store.CredentialError):
                    store.save(values)
            encrypt.assert_not_called()

    def test_exclusive_write_contains_ciphertext_only(self):
        values = dict(zip(store.ROLES,('a'*24,'b'*24)))
        raw = json.dumps({'project':store.PROJECT,'version':1,'passwords':values},allow_nan=False).encode()
        path = MagicMock()
        with patch.object(store,'STORE',path), patch.object(store,'dpapi',side_effect=[b'encrypted',raw]):
            store.save(values)
        path.open.assert_called_once_with('xb')
        path.open.return_value.__enter__.return_value.write.assert_called_once_with(b'encrypted')

    def test_foreign_project_is_rejected(self):
        path = Mock()
        path.is_symlink.return_value = False
        path.is_file.return_value = True
        with patch.object(store,'STORE',path),patch.object(store,'dpapi',return_value=b'{"project":"other","version":1,"passwords":{}}'):
            with self.assertRaisesRegex(store.CredentialError,'^local_credentials_unavailable$'):
                store.load()

    def test_runtime_config_is_fixed_and_password_redacted(self):
        with patch.object(store,'load',return_value=dict.fromkeys(store.ROLES,'synthetic-password-24-characters')):
            config = store.database_config('gather_worker')
            self.assertEqual(config.host,store.HOST)
            self.assertEqual(config.user,'gather_worker.'+store.PROJECT)
            self.assertNotIn('synthetic-password',repr(config))
            with self.assertRaises(store.CredentialError):
                store.database_config('postgres')


if __name__=='__main__':
    unittest.main()
