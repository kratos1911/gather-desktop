"""HTTP -> real coordinators -> synthetic repository/provider. NOT SQL/RLS proof."""
import base64
import hashlib
import http.client
import json
import threading
import time
import unittest
from uuid import uuid4
from unittest.mock import Mock

from services.worker.library_api import LibraryAPI
from services.worker.library_server import create_server
from services.worker.library_session import LibrarySession
from services.worker.service_clients import SessionClient
from services.worker.ingestion_repository import RepositoryError
from services.worker.worker_lifecycle import WorkerRun
from tests.worker.test_search import Provider


class FixtureStore:
    """One-source test double; never imported by application code."""
    def __init__(self):
        self.owner = self.job = self.item = self.key = None
        self.deleted = False
        self.passages, self.vectors = [], set()
        self.automatic = False

    def call(self, name, *args, owner=None):
        if name == 'submit_automatic_text':
            result = self.call('submit_text',*args,owner=owner)
            self.automatic = True
            return dict(result,automatic_processing=True)
        if name == 'next_automatic_text_job':
            return self.job['id'] if self.automatic and not self.deleted and self.job['state']=='queued' else None
        if name == 'claim_automatic_text_job':
            if not self.automatic or args[0]!=self.job['id']: return None
            name = 'claim_text_job'
        if name == 'submit_text':
            request, title, raw, media, parser, chunker, model, revision, dimensions, source = args
            if self.key == (owner,request):
                if raw != self.raw: raise RepositoryError('invalid_input')
                return self.item
            if self.item is not None: raise RepositoryError('invalid_input')
            self.key, self.owner, self.raw, self.title = (owner,request), owner, raw, title
            self.item = dict(source_id=str(uuid4()),version_id=str(uuid4()),job_id=str(uuid4()))
            self.job = dict(id=self.item['job_id'],version_id=self.item['version_id'],owner_id=owner,
                lease_token=str(uuid4()),media_type=media,input_bytes=len(raw),content_sha256=hashlib.sha256(raw).hexdigest(),
                parser_version=parser,chunker_version=chunker,model_id=model,model_revision=revision,dimensions=dimensions,state='queued')
            return self.item
        if name == 'claim_text_job':
            if self.job is None or self.deleted or self.job['state'] != 'queued': return None
            self.job['state'] = 'processing'
            return dict(self.job)
        if self.deleted: raise RepositoryError('stale_lease')
        if name == 'read_job_original': return self.raw.hex()
        if name == 'renew_text_job': return None
        if name == 'stage_text': self.passages = args[-1]; return None
        if name == 'completed_passages': return list(self.vectors)
        if name == 'stage_vectors': self.vectors.update(p['id'] for p in args[-1]); return None
        if name == 'publish_text':
            assert set(p['id'] for p in self.passages) == self.vectors
            self.job['state'] = 'ready'
            return self.item['version_id']
        if name == 'fail_text_job': self.job['state']='failed'; return 'failed'
        raise AssertionError('unexpected fixture operation')

    def rpc(self, owner, path, payload):
        if path.endswith('list_source_cleanup'):
            return [{'source_id':self.item['source_id']}] if self.deleted and owner==self.owner else []
        if path.endswith('complete_source_cleanup'):
            return self.deleted and owner==self.owner and payload['p_source']==self.item['source_id']
        visible = self.item is not None and owner == self.owner and not self.deleted
        if path.endswith('request_source_deletion'):
            if not visible or payload['p_source_id'] != self.item['source_id']: return False
            self.deleted = True
            return True
        if not visible: return []
        if path.endswith('list_library_sources'):
            return [dict(source_id=self.item['source_id'],title=self.title,kind='file',
                created_at='2026-10-26T01:00:00.000001Z',job_id=self.job['id'],
                processing_version_id=self.item['version_id'],state=self.job['state'],attempts=1,error_code=None,
                published_version_id=self.item['version_id'] if self.job['state']=='ready' else None)]
        if path.endswith('source_processing_status'):
            if payload['p_source'] != self.item['source_id']: return []
            return [dict(job_id=self.job['id'],version_id=self.item['version_id'],state=self.job['state'],attempts=1,error_code=None)]
        if self.job['state'] != 'ready': return []
        doc = dict(source_id=self.item['source_id'],version_id=self.item['version_id'],title=self.title,
            source_sha256=self.job['content_sha256'],model_id=self.job['model_id'],model_revision=self.job['model_revision'],
            dimensions=self.job['dimensions'],body=self.raw.decode(),passages=self.passages)
        if path.endswith('open_published_text'):
            return [doc] if (payload['p_source'],payload['p_version']) == (doc['source_id'],doc['version_id']) else []
        if path.endswith('search_published_text'):
            p = self.passages[0]
            return [dict(doc,passage_id=p['id'],start_offset=p['start'],end_offset=p['end'],body=doc['body'][p['start']:p['end']],similarity=1.)]
        raise AssertionError('unexpected fixture route')


class FlowTests(unittest.TestCase):
    def test_queued_then_worker_ready_then_search_open_delete_over_http(self):
        self._exercise()

    def test_opt_in_markdown_admission_uses_existing_flow_without_live_inference(self):
        self._exercise(private_files=True)

    def test_automatic_import_publishes_without_a_manual_worker_command(self):
        self._exercise(private_files=True,automatic=True)

    def _exercise(self, private_files=False, automatic=False):
        from scripts.operator_library import PILOT_USERS, PilotSession, PilotWorker
        from services.worker.automatic_processing import AutomaticAdmission, AutomaticDispatcher
        store, provider = FixtureStore(), Provider()
        dispatcher = AutomaticDispatcher(store,lambda job:WorkerRun(PilotWorker(store,job,text_files=True,automatic=True),provider),lambda:True) if automatic else None
        provider.check_ready = Mock(return_value={'state':'ready','used':0,'limit':3})
        owners = dict(zip(('a','b'),sorted(PILOT_USERS))) if private_files else {key:str(uuid4()) for key in ('a','b')}
        def session(token,cancel):
            api = Mock(spec=SessionClient)
            def request(method,path,payload=None):
                if token not in owners: raise ValueError('invalid fixture session')
                if path == '/auth/v1/user': return {'id':owners[token]}
                return store.rpc(owners[token],path,payload)
            api.side_effect = request
            def admission(owner):
                repo = Mock()
                repo.call.side_effect = lambda name,*args:store.call(name,*args,owner=owner)
                return AutomaticAdmission(repo) if automatic else repo
            return PilotSession(api,admission,provider,text_files=True,dispatcher=dispatcher) if private_files else LibrarySession(api,admission,provider)
        app = LibraryAPI(session,dispatcher=dispatcher)
        server = create_server(app,port=0)
        thread = threading.Thread(target=server.run,daemon=True)
        thread.start()
        end = time.monotonic()+5
        while not server.started and time.monotonic()<end: time.sleep(.01)
        self.assertTrue(server.started)
        port = server.servers[0].sockets[0].getsockname()[1]
        def call(route,value,token='a'):
            conn = http.client.HTTPConnection('127.0.0.1',port,timeout=4)
            try:
                conn.request('POST','/v1/'+route,json.dumps(value),{'Authorization':'Bearer '+token,'Content-Type':'application/json'})
                response = conn.getresponse()
                self.assertIn(response.status,(200,202))
                return json.loads(response.read())
            finally: conn.close()
        try:
            self.assertEqual(call('model-status',{})['state'],'ready')
            self.assertEqual(provider.calls,[])
            original = '\ufeffSynthetic database note.\r\nOwnership protects records 🌟.'
            submission = dict(request_id=str(uuid4()),title='Synthetic flow',media='text/plain',content_base64=base64.b64encode(original.encode()).decode())
            if private_files:
                submission.update(media='text/markdown',confirm_cloud_storage=True)
            item = call('import',submission)
            self.assertEqual(call('import',submission),item)
            sid,vid = item['source_id'],item['version_id']
            if not automatic:
                self.assertEqual(call('status',{'source_id':sid})[0]['state'],'queued')
                self.assertEqual(call('list',{'limit':20})['items'][0]['state'],'queued')
            self.assertEqual(call('list',{'limit':20},'b')['items'],[])
            if automatic:
                self.assertTrue(item['automatic_processing'])
                deadline = time.monotonic()+3
                while store.job['state']!='ready' and time.monotonic()<deadline: time.sleep(.01)
            else:
                self.assertEqual(call('search',{'query':'database security'})['windows'],[])
                self.assertEqual(WorkerRun(store,provider).run()['outcomes'][0]['state'],'ready')
            self.assertEqual(call('status',{'source_id':sid})[0]['state'],'ready')
            self.assertEqual(call('list',{'limit':20})['items'][0]['published_version_id'],vid)
            found = call('search',{'query':'database security'})['windows'][0]
            self.assertEqual(found['text'],original)
            self.assertEqual(found['end'],len(original))
            self.assertEqual(call('open',{'source_id':sid,'version_id':vid})[0]['body'],original)
            self.assertEqual(call('open',{'source_id':sid,'version_id':str(uuid4())}),[])
            for route,payload,expected in (
                ('status',{'source_id':sid},[]),('open',{'source_id':sid,'version_id':vid},[]),('delete',{'source_id':sid},False)):
                self.assertEqual(call(route,payload,'b'),expected)
            self.assertEqual(call('search',{'query':'database security'},'b')['windows'],[])
            self.assertTrue(call('delete',{'source_id':sid}))
            self.assertEqual(call('list',{'limit':20})['items'],[])
            model_calls = len(provider.calls)
            self.assertEqual(call('search',{'query':'database security'})['windows'],[])
            self.assertEqual(len(provider.calls),model_calls)
            self.assertEqual(WorkerRun(store,provider).run()['outcomes'],[{'state':'idle'}])
        finally:
            server.servers[0].get_loop().call_soon_threadsafe(app.stop)
            server.should_exit = True
            thread.join(8)
            self.assertFalse(thread.is_alive())
