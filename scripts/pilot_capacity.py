"""Approved Gather-only warm capacity, scoped to a supervised operator run."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT/'output/pilot-warm-scaling.json'


class CapacityError(Exception):
    pass


def set_minimum(value):
    if type(value) is not int or value not in (0,1):
        raise CapacityError('invalid_pilot_minimum')
    executable = shutil.which('gcloud.cmd')
    if executable is None:
        raise CapacityError('pilot_gcloud_unavailable')
    try:
        command = [executable,'run','services','update','gather-inference-pilot',
            '--min='+str(value),'--max=1','--region=asia-south1',
            '--project=gather-development-511211','--account=kpanigrahi5602@gmail.com']
        if value==1:
            command.append('--async')  # Readiness is observed under the separate startup budget.
        result = subprocess.run(command,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45)
        if result.returncode:
            raise ValueError()
    except subprocess.TimeoutExpired:
        raise CapacityError('pilot_scaling_update_timeout') from None
    except Exception:
        raise CapacityError('pilot_scaling_update_failed') from None


def ready_state(value):
    metadata, status = value.get('metadata',{}),value.get('status',{})
    if metadata.get('name')!='gather-inference-pilot' or metadata.get('namespace')!='119730530113':
        raise CapacityError('pilot_capacity_target_mismatch')
    generation, observed = metadata.get('generation'),status.get('observedGeneration')
    annotations = metadata.get('annotations',{})
    ready = any(c.get('type')=='Ready' and c.get('status')=='True' for c in status.get('conditions',[]))
    return (type(generation) is int and type(observed) is int and observed>=generation and ready
            and annotations.get('run.googleapis.com/minScale')=='1'
            and annotations.get('run.googleapis.com/maxScale')=='1')


def wait_ready(deadline):
    """Observe accepted configuration, not model/inference retries. Shared startup budget."""
    executable = shutil.which('gcloud.cmd')
    if executable is None:
        raise CapacityError('pilot_gcloud_unavailable')
    for _ in range(12):
        remaining = deadline-time.monotonic()
        if remaining<=0:
            break
        try:
            result = subprocess.run([executable,'run','services','describe','gather-inference-pilot',
                '--region=asia-south1','--project=gather-development-511211',
                '--account=kpanigrahi5602@gmail.com',
                '--format=json(metadata.name,metadata.namespace,metadata.generation,metadata.annotations,status.observedGeneration,status.conditions)'],
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=min(10,remaining))
            if result.returncode or len(result.stdout)>65536:
                raise ValueError()
            if ready_state(json.loads(result.stdout)):
                return
        except CapacityError:
            raise
        except Exception:
            raise CapacityError('pilot_capacity_status_unavailable') from None
        remaining = deadline-time.monotonic()
        if remaining>0:
            time.sleep(min(2,remaining))
    raise CapacityError('pilot_capacity_ready_timeout')


def record(minimum, pending):
    RECEIPT.parent.mkdir(parents=True,exist_ok=True)
    RECEIPT.write_text(json.dumps(dict(project='gather-development-511211',
        service='gather-inference-pilot',minimum=minimum,maximum=1,
        restore_minimum_zero_pending=pending,observed_utc=datetime.now(timezone.utc).isoformat()),indent=2),encoding='utf-8')


@contextmanager
def warm_instance():
    record(1,True)
    try:
        print('Keeping one Gather instance warm during this run; minimum zero will be restored on exit.')
        set_minimum(1)
        yield
    finally:
        try:
            set_minimum(0)
        except BaseException:
            raise CapacityError('pilot_minimum_zero_restore_unverified') from None
        record(0,False)
        print('Gather minimum restored to zero; scale-to-zero enabled.')
