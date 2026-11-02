"""Isolated Linux-image fixture: verified tokenizer/PDF and real local DB helpers.

No cloud identity, model loading, URL selection or production provider fallback.
The disposable DB harness alone supplies temporary loopback credentials on stdin.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
from uuid import uuid4

from services.worker.database_transport import DatabaseConfig,DatabaseRepository
from services.worker.ingestion import submit,Lease
from services.worker.ingestion_repository import RepositoryError
from services.worker.worker_lifecycle import WorkerRun
from services.worker.automatic_processing import StartupProvider
from services.worker.cloud_provider import pinned_token_counter
from services.inference.runtime import MODEL,REVISION,DIMENSIONS


def main():
    if sys.platform!='linux' or os.environ.get('K_SERVICE'):raise ValueError('disposable_fixture_only')
    raw=sys.stdin.buffer.read(16385)
    if len(raw)>16384:raise ValueError('fixture_wire_limit')
    wire=json.loads(raw)
    configs={key:DatabaseConfig(**value) for key,value in wire['configs'].items()}
    if any(not c.test_loopback or c.host!='127.0.0.1' or c.port!=5432 for c in configs.values()):
        raise ValueError('disposable_loopback_only')
    original=base64.b64decode(wire['pdf'],validate=True)
    if hashlib.sha256(original).hexdigest()!='180fed63e0df1688b6d0edfc650e59cfb0f1d50148ddc510b9bc15629bb5a3f5':
        raise ValueError('generated_fixture_changed')
    count=pinned_token_counter(Path('/app/tokenizer'))
    admission=DatabaseRepository(configs['gather_admission'],owner=wire['owner'])
    worker=DatabaseRepository(configs['gather_worker'],reuse_worker=True)
    submit(admission,request_id=str(uuid4()),title='Synthetic Linux memory fixture',original=original,media='application/pdf')
    class FixtureProvider:
        count_tokens=staticmethod(count)
        def infer(self,request,*,cancel):
            if cancel.is_set():raise RuntimeError('fixture_cancelled')
            return dict(model=MODEL,revision=REVISION,dimensions=DIMENSIONS,
                data=[dict(index=0,embedding=[1.0]+[0.0]*(DIMENSIONS-1))])
    class ImmediateHeartbeat(Lease):
        def _heartbeat(self):
            try:self.renew()
            except RepositoryError:return
            self.stopped.wait()
    with patch('services.worker.ingestion.Lease',ImmediateHeartbeat):
        result=WorkerRun(worker,StartupProvider(FixtureProvider(),lambda cancel:None,background=True),
                         record_timings=True).run()['outcomes'][0]
    if result['state']!='ready' or result['timing']['database']['helpers_started']!=2:
        raise ValueError('linux_worker_fixture_failed')
    print(json.dumps({'passed':True,'scope':'512 MiB/1 CPU, actual local SQL sessions and pinned tokenizer/PDF',
        'timing':result['timing'],'real_model_requests':0}))


if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('linux_worker_fixture_failed; no credentials or document content printed') from None
