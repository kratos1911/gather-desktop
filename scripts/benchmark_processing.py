"""Opt-in before/after check of one existing, generated PDF; no private files.

The operator enters pilot B's password locally. Tokens stay in memory while the
assistant updates the approved candidate flags. No import or inference retry.
"""
import argparse
import base64
from datetime import datetime, timezone
import getpass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from uuid import uuid4
import warnings

from services.worker.service_transport import request_json
from services.worker.processing_timing import safe_timing
from scripts.check_hosted_flow import configuration

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/processing-speed'
API='https://gather-library-pilot-119730530113.asia-south1.run.app'
AUTH='https://fatolholcjxpwocnpzws.supabase.co'
PROJECT='gather-development-511211'
ACCOUNT='kpanigrahi5602@gmail.com'
USER='903b7ed0-9d21-467c-907a-4032d589f4c4'
EMAIL='gather-pilot-b@example.invalid'
TITLE='hosted-pilot.pdf'
SHA='180fed63e0df1688b6d0edfc650e59cfb0f1d50148ddc510b9bc15629bb5a3f5'
BODY='Orchard backups are kept for fourteen days.\n\nArchive requests belong on page two.'


class Stopped(Exception):pass


def require(condition,code):
    if not condition:raise Stopped(code)


def utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')


def cloud(*args):
    executable=shutil.which('gcloud.cmd')
    require(executable is not None,'gcloud_unavailable')
    result=subprocess.run([executable,*args,'--project='+PROJECT,'--account='+ACCOUNT,'--format=json','--quiet'],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    require(result.returncode==0 and len(result.stdout)<=1024*1024,'cloud_read_unavailable')
    return json.loads(result.stdout)


def service_mode(optimized):
    value=cloud('run','services','describe','gather-library-pilot','--region=asia-south1')
    container=value['spec']['template']['spec']['containers'][0]
    proof=json.loads((OUT/'image-verification.json').read_text(encoding='utf-8-sig'))
    require(proof.get('passed') is True and container['image'].endswith('@'+proof['image']),'unverified_api_revision')
    env={row['name']:row.get('value') for row in container.get('env',[])}
    require(env.get('GATHER_PIPELINE_TIMING')=='1'
        and env.get('GATHER_WORKER_DB_REUSE')==('1' if optimized else '0')
        and env.get('GATHER_EARLY_MODEL_START')==('1' if optimized else '0'),'unexpected_pipeline_mode')
    return value['status']['latestReadyRevisionName']


def call(token,operation,payload):
    # Existing transport's 15s whole-request limit; never resend on uncertainty.
    return request_json(API,'/v1/'+operation,{'Authorization':'Bearer '+token},
                        payload,timeout=15,expected_status=202 if operation=='import' else 200)


def fixture_source(token):
    page=call(token,'list',{'limit':20})
    matches=[row for row in page['items'] if row['title']==TITLE]
    require(len(matches)==1 and page['next_cursor'] is None,'generated_source_not_unique')
    source=matches[0]
    require(source['state']=='ready' and source['processing_version_id']==source['published_version_id'],
            'generated_source_not_ready')
    docs=call(token,'open',{'source_id':source['source_id'],'version_id':source['published_version_id']})
    require(type(docs) is list and len(docs)==1 and docs[0].get('source_sha256')==SHA
            and docs[0].get('body')==BODY,'generated_fixture_changed')
    return source


def collect_logs(revision,started,ended,expected_calls):
    value={'classification':'not_measured'}
    try:
        entries=cloud('logging','read',
            'resource.type="cloud_run_revision" AND resource.labels.revision_name="'+revision+
            '" AND timestamp>="'+started+'" AND timestamp<="'+ended+
            '" AND textPayload:"Automatic processing:"','--limit=8')
        candidates=[]
        for row in entries:
            text=row.get('textPayload','')
            if not text.startswith('Automatic processing: '):continue
            data=json.loads(text[len('Automatic processing: '):])
            if data.get('states')==['ready']:
                timings=data.get('timings',[])
                if len(timings)==1 and safe_timing(timings[0]) is not None:
                    candidates.append((row,data,timings[0]))
        if len(candidates)==1:
            row,data,measurement=candidates[0]
            value.update(timing=measurement,ready_log_utc=row['timestamp'],
                         instance_model_counter=data.get('model_attempts_used'))
        elif candidates:value['log_capture']='ambiguous_ready_events'
        upper=value.get('ready_log_utc',ended)
        starts=cloud('logging','read',
            'resource.type="cloud_run_revision" AND resource.labels.service_name="gather-inference-pilot"'
            ' AND timestamp>="'+started+'" AND timestamp<="'+upper+'" AND textPayload:"Starting new instance"',
            '--limit=4')
        value['classification']='cold_start_observed' if starts else 'no_cold_start_observed'
    except Exception:
        value['log_capture']='unavailable'  # Keep outcome; never rerun a model to fill a log gap.
    return value


def run_sample(token,source,raw,mode,index,revision,receipt,save,*,recover_ack=False):
    if recover_ack:
        entry=receipt['samples'][0]
        require(mode=='baseline' and index==1 and entry['stage']=='import'
                and entry['mode']==mode and entry['sample']==index,'unsupported_ack_recovery')
        entry.update(harness_interrupted=True,resumed_utc=utc())
    else:
        entry={'mode':mode,'sample':index,'request_id':str(uuid4()),'stage':'import',
               'started_utc':utc(),'ready':False}
        receipt['samples'].append(entry)
    save()
    started=time.monotonic()
    item=call(token,'import',{'request_id':entry['request_id'],'source_id':source['source_id'],
        'title':TITLE,'media':'application/pdf','content_base64':base64.b64encode(raw).decode(),
        'confirm_cloud_storage':True})
    entry['ack_recovery_ms' if recover_ack else 'admission_ms']=round((time.monotonic()-started)*1000,2)
    require(item.get('source_id')==source['source_id'] and item.get('automatic_processing') is True,
            'unexpected_import_receipt')
    if recover_ack:
        require(item['version_id']==source['published_version_id'],'recovered_import_is_not_the_verified_publication')
    entry.update(stage='processing',job_id=item['job_id'],version_id=item['version_id']);save()
    deadline=time.monotonic()+300
    for _ in range(30):
        states=call(token,'status',{'source_id':source['source_id']})
        matching=[r for r in states if r['job_id']==item['job_id'] and r['version_id']==item['version_id']]
        require(len(matching)==1,'job_superseded_or_unavailable')
        state=matching[0]
        if state['state']=='ready':break
        require(state['state'] not in ('failed','cancelled')
                and not (state['state']=='queued' and state['attempts']>0),'processing_requires_explicit_recovery')
        require(time.monotonic()<deadline,'processing_observation_deadline')
        time.sleep(min(10,max(0,deadline-time.monotonic())))
    else:raise Stopped('processing_poll_limit')
    entry.update(ready=True,stage='open',observed_seconds=None if recover_ack else round(time.monotonic()-started,2),
                 completed_utc=utc(),attempts=state['attempts']);save()
    docs=call(token,'open',{'source_id':source['source_id'],'version_id':item['version_id']})
    require(len(docs)==1 and docs[0]['body']==BODY and docs[0]['source_sha256']==SHA,
            'published_fixture_mismatch')
    require(state['attempts']==1 and len(docs[0].get('passages',[]))==1,'unexpected_attempt_or_passage_count')
    entry.update(stage='complete',exact_open_verified=True,
        log=collect_logs(revision,entry['started_utc'],entry['completed_utc'],index))
    save()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--resume-ack',action='store_true',help='Recover only the reviewed HTTP202 acknowledgement failure, keeping its request ID.')
    args=parser.parse_args()
    require(not args.resume_ack or args.run,'ack_recovery_requires_run')
    if not args.run:
        print('Preview: pilot B; replace only the known generated hosted-pilot.pdf version, twice per mode.')
        print('At most four real embeddings; no searches/deletions/new sources/model changes. Local password prompt.')
        return
    raw=(ROOT/'output/pdf-pilot/hosted-pilot.pdf').read_bytes()
    require(len(raw)==1090 and hashlib.sha256(raw).hexdigest()==SHA,'local_generated_fixture_changed')
    OUT.mkdir(parents=True,exist_ok=True)
    active=OUT/'active-benchmark.json'
    recovered=None;recovered_path=None
    if args.resume_ack:
        pointer=json.loads(active.read_text(encoding='utf-8-sig'))
        recovered_path=Path(pointer['receipt']).resolve()
        require(recovered_path.is_relative_to(OUT.resolve()),'invalid_benchmark_receipt_path')
        recovered=json.loads(recovered_path.read_text(encoding='utf-8-sig'))
        require(recovered.get('stage')=='stopped' and recovered.get('sha256')==SHA
                and len(recovered.get('samples',[]))==1
                and recovered['samples'][0].get('stage')=='import'
                and recovered.get('error')=='benchmark_operation_failed','ack_recovery_receipt_not_eligible')
    elif active.exists():
        previous=json.loads(active.read_text(encoding='utf-8-sig'))
        require(previous.get('complete') is True,'unfinished_benchmark_receipt_review_required')
    revision=service_mode(False)
    key=configuration()
    warnings.simplefilter('error',getpass.GetPassWarning)
    password=getpass.getpass('Existing pilot B password (hidden): ')
    try:
        try:
            session=request_json(AUTH,'/auth/v1/token?grant_type=password',{'apikey':key},
                {'email':EMAIL,'password':password},timeout=5)
        except Exception:raise Stopped('pilot_b_signin_failed') from None
    finally:password=None
    token=session['access_token'];session=None
    try:
        owner=request_json(AUTH,'/auth/v1/user',{'apikey':key,'Authorization':'Bearer '+token},None,timeout=5)
        require(owner.get('id')==USER,'pilot_b_required')
        source=fixture_source(token)
        if recovered is not None:
            require(recovered['source_id']==source['source_id'] and recovered['baseline_revision']==revision,
                    'ack_recovery_target_changed')
            path=recovered_path;receipt=recovered
            receipt.setdefault('harness_events',[]).append({'error':receipt.pop('error'),'resolution':'explicit_idempotent_ack_recovery'})
            receipt['stage']='baseline'
        else:
            path=OUT/('hosted-'+uuid4().hex+'.json')
            receipt={'scope':'Generated PDF only; real Auth, hosted DB and CPU embeddings',
                 'source_id':source['source_id'],'sha256':SHA,'samples':[],
                 'baseline_revision':revision,'complete':False,'stage':'baseline'}
        def save():
            path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
            active.write_text(json.dumps({'receipt':str(path),'stage':receipt['stage'],
                                         'complete':receipt['complete']},indent=2),encoding='utf-8')
        save()
        try:
            for index in (1,2):
                run_sample(token,source,raw,'baseline',index,revision,receipt,save,
                           recover_ack=args.resume_ack and index==1)
            status=call(token,'model-status',{})
            require(status.get('limit')==3 and 0<=status.get('used',-1)<=3,'invalid_baseline_model_status')
            receipt['baseline_model_status']=status;save()
            receipt['stage']='awaiting_optimized_deployment';save()
            print('Baseline complete. Waiting for the approved optimized API revision; no model calls while waiting.',flush=True)
            deadline=time.monotonic()+900
            while True:
                candidate=OUT/'deployment-optimized.json'
                if candidate.exists():
                    update=json.loads(candidate.read_text(encoding='utf-8-sig'))
                    if update.get('completed') is True and update.get('previous_revision')==revision:break
                require(time.monotonic()<deadline,'candidate_deployment_wait_expired')
                time.sleep(1)
            revision=service_mode(True)
            receipt.update(stage='optimized',optimized_revision=revision);save()
            for index in (1,2):run_sample(token,source,raw,'optimized',index,revision,receipt,save)
            status=call(token,'model-status',{})
            require(status.get('limit')==3 and 0<=status.get('used',-1)<=3,'invalid_optimized_model_status')
            receipt['optimized_model_status']=status
            # Logging can arrive after the response. Fill missing metrics using
            # read-only queries; never rerun ingestion/inference for missing logs.
            for sample in receipt['samples']:
                if 'timing' not in sample.get('log',{}):
                    source_revision=receipt['baseline_revision'] if sample['mode']=='baseline' else revision
                    sample['log']=collect_logs(source_revision,sample['started_utc'],
                                              sample['completed_utc'],sample['sample'])
            receipt.update(complete=True,stage='complete',maximum_model_requests=4,
                           private_files_touched=False,deletions=False,new_sources=False);save()
            print('Comparison complete. Safe receipt: '+str(path),flush=True)
        except Exception as error:
            receipt['error']=str(error) if isinstance(error,Stopped) else 'benchmark_operation_failed'
            receipt['stage']='stopped';save()
            raise
    finally:token=None


if __name__=='__main__':
    try:main()
    except Exception as error:
        code=str(error) if isinstance(error,Stopped) else 'benchmark_operation_failed'
        raise SystemExit(code+'. No automatic retry; inspect the safe receipt, never passwords or tokens.') from None
