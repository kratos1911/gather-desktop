import unittest
from services.worker.network_policy import approve_destination


class NetworkPolicyTests(unittest.TestCase):
    def test_public_dns_and_deduplication(self):
        called = []
        def resolver(host, port):
            called.append((host, port))
            return ['8.8.8.8', '8.8.8.8', '1.1.1.1']
        result = approve_destination('https://example.com/page?q=1', resolver)
        self.assertEqual(called, [('example.com', 443)])
        self.assertEqual(result.addresses, ('1.1.1.1', '8.8.8.8'))
        self.assertEqual(result.url, 'https://example.com/page?q=1')

    def test_mixed_public_private_dns_denied(self):
        with self.assertRaisesRegex(ValueError, 'DESTINATION_ADDRESS_DENIED'):
            approve_destination('https://example.com', lambda *_: ['8.8.8.8', '10.0.0.1'])

    def test_private_metadata_and_special_ranges(self):
        for address in ['127.0.0.1', '169.254.169.254', '192.168.1.1', '100.64.0.1', '::1', 'fc00::1', 'fe80::1', '224.0.0.1', '::ffff:8.8.8.8']:
            with self.subTest(address=address), self.assertRaises(ValueError):
                approve_destination('https://example.com', lambda *_: [address])

    def test_empty_invalid_and_unbounded_answers(self):
        for addresses in [[], ['bad'], ['fe80::1%eth0'], ['8.8.8.8'] * 33, '8.8.8.8']:
            with self.subTest(addresses=addresses), self.assertRaises(ValueError):
                approve_destination('https://example.com', lambda *_: addresses)

    def test_literal_skips_dns(self):
        def resolver(*_):
            raise AssertionError('must not resolve literal')
        self.assertEqual(approve_destination('https://8.8.8.8', resolver).addresses, ('8.8.8.8',))

    def test_unsafe_schemes_credentials_ports_and_numeric_hosts(self):
        for url in ['file:///secret', 'https://u:p@example.com', 'http://example.com:0', 'http://example.com:22', 'http://0177.0.0.1']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                approve_destination(url, lambda *_: ['8.8.8.8'])

    def test_dns_errors_are_sanitized(self):
        def resolver(*_):
            raise RuntimeError('private-secret')
        with self.assertRaisesRegex(ValueError, '^DESTINATION_DNS_FAILED$'):
            approve_destination('https://example.com', resolver)

    def test_revalidation_rejects_changed_destination(self):
        approve_destination('https://example.com', lambda *_: ['8.8.8.8'])
        with self.assertRaises(ValueError):
            approve_destination('https://example.com', lambda *_: ['127.0.0.1'])


if __name__ == '__main__':
    unittest.main()
