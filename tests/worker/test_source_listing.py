"""Synthetic metadata/session checks, not hosted Auth/RLS evidence."""
import base64
import json
import unittest
from unittest.mock import Mock, patch

from services.worker.source_listing import page, parameters
from services.worker.library_session import LibrarySession, LibraryError
from services.worker.service_clients import SessionClient
from tests.worker.test_service_clients import token

OWNER = '00000000-0000-0000-0000-000000000001'


def row(n=3, **changes):
    return dict(source_id=f'00000000-0000-0000-0000-{n:012d}',title='Synthetic metadata',kind='file',
                created_at='2026-10-26T01:00:00.000001Z',published_version_id=None,
                processing_version_id=None,job_id=None,state=None,attempts=None,error_code=None,**changes)


class ListingTests(unittest.TestCase):
    def test_lookahead_cursor_and_tied_timestamps(self):
        first = page([row(3),row(2),row(1)],2)
        self.assertEqual(len(first['items']),2)
        self.assertEqual(parameters(2,first['next_cursor'])['p_before_id'],row(2)['source_id'])
        last = page([row(1)],2,first['next_cursor'])
        self.assertIsNone(last['next_cursor'])
        self.assertEqual(page([]),{'items':[],'next_cursor':None})

    def test_invalid_cursors_and_limits(self):
        def encode(value):
            return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')
        for cursor in ('','a'*257,'@',encode({'v':1,'created_at':'infinity','source_id':OWNER}),
                       encode({'v':True,'created_at':row()['created_at'],'source_id':OWNER}),
                       encode({'v':1,'created_at':row()['created_at'],'source_id':OWNER,'owner':OWNER})):
            with self.subTest(cursor=cursor[:30]), self.assertRaises(ValueError): parameters(cursor=cursor)
        for limit in (0,21,True,1.5,None):
            with self.assertRaises(ValueError): parameters(limit)

    def test_rejects_private_fields_bad_order_and_invalid_publication(self):
        for rows in ([dict(row(),original='secret')],[row(1),row(2)],[row(1),row(1)],
                     [dict(row(),state='ready',job_id=OWNER,processing_version_id=OWNER,attempts=1)],
                     [dict(row(),state='processing')]):
            with self.assertRaises(ValueError): page(rows)
        cursor = page([row(3),row(2)],1)['next_cursor']
        with self.assertRaises(ValueError): page([row(3)],1,cursor)

    def test_preserves_publication_during_failed_replacement(self):
        value = dict(row(),published_version_id=OWNER,processing_version_id=row()['source_id'],
                     job_id=OWNER,state='failed',attempts=3,error_code='invalid_input')
        self.assertEqual(page([value])['items'][0],value)

    def test_listing_verifies_auth_for_every_page_and_never_embeds(self):
        api = Mock(spec=SessionClient)
        api.side_effect = [{'id':OWNER},[row(3),row(2)],{'id':OWNER},[row(1)]]
        provider, admission = Mock(),Mock()
        session = LibrarySession(api,admission,provider)
        first = session.list_sources(limit=1)
        session.list_sources(limit=1,cursor=first['next_cursor'])
        self.assertEqual([c.args[1] for c in api.call_args_list],[
            '/auth/v1/user','/rest/v1/rpc/list_library_sources_with_recovery']*2)
        self.assertNotIn('owner',api.call_args.kwargs)
        provider.infer.assert_not_called()
        admission.assert_not_called()
        api.side_effect = RuntimeError('private credentials')
        with self.assertRaisesRegex(LibraryError,'^session_unavailable$'): session.list_sources()

    def test_session_client_fixed_route_uses_original_bearer(self):
        bearer = token('authenticated')
        api = SessionClient('https://example.supabase.co','sb_publishable_fixture',bearer)
        with patch('services.worker.service_clients.request_json',return_value=[]) as send:
            api('POST','/rest/v1/rpc/list_library_sources',parameters())
            self.assertEqual(send.call_args.args[2]['Authorization'],'Bearer '+bearer)
            self.assertEqual(send.call_args.kwargs['timeout'],5)
        with self.assertRaises(Exception):
            api('POST','/rest/v1/rpc/list_library_sources',dict(parameters(),owner=OWNER))

    def test_recovery_hint_is_bounded_and_cannot_make_a_completed_job_resumable(self):
        value=dict(row(),processing_version_id=OWNER,job_id=OWNER,state='processing',attempts=1,can_resume=False)
        self.assertFalse(page([value])['items'][0]['can_resume'])
        for fields in ({'can_resume':'yes'},{'can_resume':True,'attempts':3},
                       {'can_resume':True,'state':'failed'},{'can_resume':True,'job_id':None}):
            with self.subTest(fields=fields),self.assertRaises(ValueError):page([dict(value,**fields)])
