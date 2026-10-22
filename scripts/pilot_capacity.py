"""Approved Gather-only warm capacity, scoped to a supervised operator run."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

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
        result = subprocess.run([executable,'run','services','update','gather-inference-pilot',
            '--min='+str(value),'--max=1','--region=asia-south1',
            '--project=gather-development-511211','--account=kpanigrahi5602@gmail.com'],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45)
        if result.returncode:
            raise ValueError()
    except Exception:
        raise CapacityError('pilot_scaling_update_failed') from None


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
