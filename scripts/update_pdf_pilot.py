"""Reviewed PDF-only update of the existing Gather API. Preview by default."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PROJECT='gather-development-511211'
ACCOUNT='kpanigrahi5602@gmail.com'
REGION='asia-south1'
SERVICE='gather-library-pilot'
CALLER='gather-pilot-caller@'+PROJECT+'.iam.gserviceaccount.com'
PREVIOUS='sha256:522826fd030d34807e17c2073c1b23d8376a30d215d936f738e74f83a4cc3724'


def plan():
    verified=json.loads((ROOT/'output/pdf-pilot/image-verification.json').read_text(encoding='utf-8-sig'))
    image=verified['image']
    if not re.fullmatch('sha256:[0-9a-f]{64}',image) or verified.get('passed') is not True:
        raise ValueError('unverified_pdf_image')
    return dict(project=PROJECT,region=REGION,service=SERVICE,
        image=f'{REGION}-docker.pkg.dev/{PROJECT}/gather-pilot-images/library@{image}',
        previous_image=PREVIOUS,environment_update={'GATHER_PDF_PILOT':'1'},
        cpu=1,memory='512Mi',minimum=0,maximum=1,new_services=False,
        iam_or_secret_changes=False,model_changes=False,budget='Existing aggregate INR500 pilot allowance')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    value=plan()
    if not args.apply: print(json.dumps(value,indent=2));return
    executable=shutil.which('gcloud.cmd')
    if executable is None:raise ValueError('gcloud_unavailable')
    def call(*command):
        result=subprocess.run([executable,*command,'--project='+PROJECT,'--account='+ACCOUNT,'--region='+REGION,'--quiet'],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=240)
        if result.returncode: raise RuntimeError('gather_update_failed_'+str(result.returncode))
        return result.stdout
    current=json.loads(call('run','services','describe',SERVICE,'--format=json'))
    template=current['spec']['template'];container=template['spec']['containers'][0]
    annotations={**template['metadata'].get('annotations',{}),**current['metadata'].get('annotations',{})}
    if (not container['image'].endswith('@'+PREVIOUS) or template['spec']['serviceAccountName']!=CALLER
            or container['resources']['limits']!={'cpu':'1','memory':'512Mi'}
            or not any(annotations.get(key)=='1' for key in ('autoscaling.knative.dev/maxScale','run.googleapis.com/maxScale'))
            or any(annotations.get(key) not in (None,'0') for key in ('autoscaling.knative.dev/minScale','run.googleapis.com/minScale'))):
        raise ValueError('existing_gather_configuration_changed_review_required')
    receipt=dict(value,previous_revision=current['status'].get('latestReadyRevisionName'),completed=False)
    path=ROOT/'output/pdf-pilot/deployment.json';path.write_text(json.dumps(receipt,indent=2))
    call('run','services','update',SERVICE,'--image='+value['image'],'--update-env-vars=GATHER_PDF_PILOT=1')
    updated=json.loads(call('run','services','describe',SERVICE,'--format=json'))
    if updated['spec']['template']['spec']['containers'][0]['image']!=value['image']:
        raise RuntimeError('updated_image_not_confirmed')
    receipt.update(completed=True,revision=updated['status'].get('latestReadyRevisionName'))
    path.write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
