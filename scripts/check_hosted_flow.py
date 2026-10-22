"""Opt-in hosted pilot with synthetic content and real user sessions/cloud vectors.

Run through scripts/python.ps1 (existing tokenizer and database driver, no weights).
Passwords are hidden prompts, tokens remain in memory, safe receipt contains IDs.
"""
import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
import warnings

from scripts.check_cloud_ingestion import IDENTITY, PilotToken, BoundedProvider
from services.worker.cloud_provider import cloud_provider
from services.worker.database_transport import DatabaseRepository, ROOT
from services.worker.ingestion import run_once
from services.worker.library_session import LibrarySession
from services.worker.local_credentials import database_config, PROJECT
from services.worker.service_clients import SessionClient
from services.worker.service_transport import request_json, strict_json, credential

BASE = 'https://'+PROJECT+'.supabase.co'
EMAILS = ('gather-pilot-a@example.invalid','gather-pilot-b@example.invalid')
RAW = b'Synthetic Gather pilot note. Database records are protected through ownership checks and row-level security policies.'
QUERY = 'How is access to database records restricted?'
RECEIPT = ROOT/'output/hosted-pilot/receipt.json'


class PilotFailure(Exception):
    pass


class QueryCapture:
    """Reuse only this exact real query response for SQL isolation/deletion checks."""
    def __init__(self, provider):
        self.provider = provider
        self.count_tokens = provider.count_tokens
        self.query = self.result = None
        self.replays = 0

    def infer(self, request, *, cancel):
        if cancel is not None and cancel.is_set():
            raise PilotFailure('cancelled')
        if request['role']=='query' and self.result is not None:
            if request != self.query:
                raise PilotFailure('query_replay_mismatch')
            self.replays += 1
            return self.result
        result = self.provider.infer(request,cancel=cancel)
        if request['role']=='query':
            self.query = {'role':request['role'],'texts':list(request['texts'])}
            self.result = result
        return result


class ExpectedWorker:
    def __init__(self, worker, job_id):
        self.worker, self.job_id = worker, job_id

    def call(self, function, *args):
        value = self.worker.call(function,*args)
        if function=='claim_text_job' and (value is None or value.get('id')!=self.job_id):
            # Do not read/process another job. Any unexpected lease expires normally.
            raise PilotFailure('unexpected_job_claim')
        return value


def require(value, code):
    if not value:
        raise PilotFailure(code)


def exercise(first, second, worker, provider, receipt, save):
    item = None
    try:
        receipt['stage'] = 'import'
        receipt['cleanup_pending'] = 'unknown_until_submission_acknowledged'
        save(receipt)
        args = dict(request_id=receipt['request_id'],title='Synthetic hosted pilot',original=RAW,media='text/plain')
        item = first.import_text(**args)
        receipt.update(item,cleanup_pending=True)
        save(receipt)
        require(first.import_text(**args)==item,'duplicate_identity')
        sid, vid = item['source_id'],item['version_id']
        require(first.status(sid)[0]['state']=='queued','queued_status')
        require(second.status(sid)==[] and second.open(sid,vid)==[],'private_draft')
        require(second.delete(sid) is False,'foreign_delete')
        receipt['stage'] = 'processing'
        save(receipt)
        result = run_once(ExpectedWorker(worker,item['job_id']),provider)
        receipt['job_outcome'] = {k:result[k] for k in ('state','error_code') if k in result}
        save(receipt)
        require(result['state']=='ready' and result['version_id']==vid,'processing_not_ready')
        require(first.status(sid)[0]['state']=='ready','published_status')
        receipt['stage'] = 'search_open'
        save(receipt)
        found = first.search(QUERY)
        require(any(w['source_id']==sid for w in found['windows']),'own_search_missing')
        opened = first.open(sid,vid)
        require(len(opened)==1 and opened[0]['body']==RAW.decode(),'original_text_mismatch')
        require(second.open(sid,vid)==[],'foreign_open')
        require(all(w['source_id']!=sid for w in second.search(QUERY)['windows']),'foreign_search')
        receipt['stage'] = 'deletion'
        save(receipt)
        require(first.delete(sid) is True,'owner_delete')
        receipt['tombstoned'] = True
        save(receipt)
        require(first.open(sid,vid)==[] and first.status(sid)==[],'deleted_read')
        require(all(w['source_id']!=sid for w in first.search(QUERY)['windows']),'deleted_search')
        receipt.update(passed=True,stage='complete')
        save(receipt)
    finally:
        if item and not receipt.get('tombstoned'):
            try:
                receipt['tombstoned'] = first.delete(item['source_id']) is True
            except Exception:
                receipt['tombstoned'] = False
            save(receipt)


def configuration():
    value = json.loads((ROOT/'output/supabase/pilot-public.json').read_text(encoding='utf-8-sig'))
    require(value.get('project_ref')==PROJECT and value.get('url')==BASE,'public_config_target')
    key = value.get('publishable_key')
    require(isinstance(key,str) and key.startswith('sb_publishable_'),'publishable_key_required')
    return key


def google_token():
    executable = shutil.which('gcloud.cmd')
    require(executable is not None,'gcloud_unavailable')
    result = subprocess.run([executable,'auth','print-identity-token',
        '--impersonate-service-account='+IDENTITY.caller_email,'--audiences='+IDENTITY.audience,
        '--include-email','--account=kpanigrahi5602@gmail.com','--project=gather-development-511211'],
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=15)
    require(result.returncode==0 and len(result.stdout)<=8192,'google_token_unavailable')
    return PilotToken(result.stdout.decode('ascii').strip())


def ready_child():
    """Separate startup probe: fixed HTTPS target, no inference or redirects."""
    from urllib.request import Request, build_opener, ProxyHandler
    from services.worker.embedding_client import _NoRedirect
    try:
        token = sys.stdin.buffer.read(7169).decode('ascii')
        require(len(token)<=7168,'invalid_token')
        credential(token)
        request = Request(IDENTITY.audience+'/ready',headers={'Authorization':'Bearer '+token,
            'X-Serverless-Authorization':'Bearer '+token,'Accept-Encoding':'identity'})
        with build_opener(ProxyHandler({}),_NoRedirect()).open(request,timeout=55) as response:
            raw = response.read(4097)
            require(response.status==200 and len(raw)<=4096,'readiness_response')
        require(strict_json(raw)=={'ready':True},'cloud_not_ready')
        print('{"ready":true}')
    except Exception:
        sys.exit(1)


def wait_for_startup(identity):
    print('Checking cloud startup: one readiness probe, at most 60 seconds. Inference remains limited to 15 seconds.')
    result = subprocess.run([sys.executable,'-I','-B','-c',
        f'import sys; sys.path.insert(0,{str(ROOT)!r}); from scripts.check_hosted_flow import ready_child; ready_child()'],
        input=identity.get().encode('ascii'),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
        cwd=ROOT,env={k:os.environ[k] for k in ('SYSTEMROOT','WINDIR') if k in os.environ},timeout=60)
    require(result.returncode==0 and len(result.stdout)<=4096 and strict_json(result.stdout)=={'ready':True},
            'cloud_startup_probe_failed')


def sign_in_clients(key):
    warnings.simplefilter('error',getpass.GetPassWarning)
    clients, owners = [], []
    for index,email in enumerate(EMAILS):
        password = getpass.getpass('Password for '+email+' (hidden): ')
        try:
            try:
                session = request_json(BASE,'/auth/v1/token?grant_type=password',{'apikey':key},
                    {'email':email,'password':password},timeout=5)
            except Exception as error:
                from services.worker.service_transport import AUTH_CODES
                safe = {code.decode() for code in AUTH_CODES} | {'timeout','rate_limited','authentication_failed','service_unavailable'}
                code = str(error) if str(error) in safe else 'signin_failed'
                raise PilotFailure('pilot_'+('a' if index==0 else 'b')+'_'+code) from None
        finally:
            del password
        client = SessionClient(BASE,key,session['access_token'])
        del session
        user = client('GET','/auth/v1/user')
        require(user['email']==email and str(uuid.UUID(user['id']))==user['id'],'pilot_user_identity')
        owners.append(user['id'])
        clients.append(client)
    require(len(set(owners))==2,'distinct_users_required')
    return clients


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--run',action='store_true')
    action.add_argument('--check-auth',action='store_true',help='Check hidden test-user logins only; no imports or model calls')
    args = parser.parse_args()
    if not args.run and not args.check_auth:
        print('Preview: one synthetic hosted TXT, two real Auth sessions, at most 3 model calls; deletion hides content, operator finalizes physical cleanup.')
        return
    if args.run:
        require(not RECEIPT.exists(),'existing_pilot_receipt_review_required')
    key = configuration()
    settings = request_json(BASE,'/auth/v1/settings',{'apikey':key},None,timeout=5)
    require(settings.get('disable_signup') is True,'disable_public_signup_first')
    clients = sign_in_clients(key)
    if args.check_auth:
        print('Both pilot user sessions verified. No document, worker or model operations performed.')
        return
    admission_config, worker_config = database_config('gather_admission'),database_config('gather_worker')
    identity = google_token()
    receipt = None
    try:
        real = BoundedProvider(cloud_provider(IDENTITY,ROOT/'output/inference-model',token_provider=identity))
        provider = QueryCapture(real)
        wait_for_startup(identity)
        libraries = [LibrarySession(client,lambda owner:DatabaseRepository(admission_config,owner=owner),provider)
                     for client in clients]
        worker = DatabaseRepository(worker_config)
        receipt = dict(project=PROJECT,request_id=str(uuid.uuid4()),passed=False,stage='preflight_complete',
            cleanup_pending=False,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
        RECEIPT.parent.mkdir(parents=True,exist_ok=True)
        def save(value):
            RECEIPT.write_text(json.dumps(value,indent=2),encoding='utf-8')
        # Exclusive creation stops automatic reruns against an uncertain prior submission.
        with RECEIPT.open('x',encoding='utf-8') as stream:
            json.dump(receipt,stream)
        try:
            exercise(*libraries,worker,provider,receipt,save)
        finally:
            receipt.update(real_model_requests=real.calls,compatible_query_replays=provider.replays)
            save(receipt)
        print(json.dumps(receipt,indent=2))
        print('Physical cleanup remains pending for the source ID in this receipt. Do not rerun automatically.')
    finally:
        identity.invalidate()
        if receipt is not None:
            print('Safe receipt: '+str(RECEIPT))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error,PilotFailure) else 'hosted_pilot_failed'
        raise SystemExit(code+'. No automatic retry; send the safe receipt/output, never passwords or tokens.') from None
