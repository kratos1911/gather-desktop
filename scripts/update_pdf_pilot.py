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


def plan(recovery=False,performance=False,optimized=False):
    verified=json.loads((ROOT/('output/processing-speed/image-verification.json' if performance else
        'output/recovery-fix/image-verification.json' if recovery else 'output/pdf-pilot/image-verification.json')).read_text(encoding='utf-8-sig'))
    image=verified['image']
    if not re.fullmatch('sha256:[0-9a-f]{64}',image) or verified.get('passed') is not True:
        raise ValueError('unverified_pdf_image')
    environment={'GATHER_PDF_PILOT':'1'}
    previous='sha256:72ce93fda395473d17dbce81247ced97f138e334ff8fef3c949cfb2ec479db8d' if recovery else PREVIOUS
    if performance:
        previous=image if optimized else 'sha256:ae5a05c14d30aa1c259f962f766ece08ec5e778635f835a64041558c84b196d1'
        environment.update(GATHER_PIPELINE_TIMING='1',GATHER_WORKER_DB_REUSE='1' if optimized else '0',
                           GATHER_EARLY_MODEL_START='1' if optimized else '0')
    return dict(project=PROJECT,region=REGION,service=SERVICE,
        image=f'{REGION}-docker.pkg.dev/{PROJECT}/gather-pilot-images/library@{image}',
        previous_image=previous,environment_update=environment,
        cpu=1,memory='512Mi',minimum=0,maximum=1,new_services=False,
        iam_or_secret_changes=False,model_changes=False,budget='Existing aggregate INR500 pilot allowance')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    parser.add_argument('--recovery',action='store_true',help='Update the deployed PDF revision with the verified recovery image.')
    parser.add_argument('--performance',action='store_true',help='Use the performance image, initially with baseline behavior.')
    parser.add_argument('--optimized',action='store_true',help='Enable verified worker reuse and earlier readiness on the performance image.')
    args=parser.parse_args()
    if (args.recovery and args.performance) or (args.optimized and not args.performance):
        parser.error('Choose one approved variant; optimized requires performance.')
    value=plan(args.recovery,args.performance,args.optimized)
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
    if (not container['image'].endswith('@'+value['previous_image']) or template['spec']['serviceAccountName']!=CALLER
            or container['resources']['limits']!={'cpu':'1','memory':'512Mi'}
            or not any(annotations.get(key)=='1' for key in ('autoscaling.knative.dev/maxScale','run.googleapis.com/maxScale'))
            or any(annotations.get(key) not in (None,'0') for key in ('autoscaling.knative.dev/minScale','run.googleapis.com/minScale'))):
        raise ValueError('existing_gather_configuration_changed_review_required')
    if args.optimized:
        environment={entry['name']:entry.get('value') for entry in container.get('env',[])}
        if any(environment.get(key)!=expected for key,expected in
               {'GATHER_PIPELINE_TIMING':'1','GATHER_WORKER_DB_REUSE':'0','GATHER_EARLY_MODEL_START':'0'}.items()):
            raise ValueError('profiled_baseline_revision_required')
    receipt=dict(value,previous_revision=current['status'].get('latestReadyRevisionName'),completed=False)
    path=ROOT/('output/processing-speed/deployment-optimized.json' if args.optimized else
        'output/processing-speed/deployment-baseline.json' if args.performance else
        'output/recovery-fix/deployment.json' if args.recovery else 'output/pdf-pilot/deployment.json')
    path.write_text(json.dumps(receipt,indent=2))
    call('run','services','update',SERVICE,'--image='+value['image'],
         '--update-env-vars='+','.join(key+'='+entry for key,entry in value['environment_update'].items()))
    updated=json.loads(call('run','services','describe',SERVICE,'--format=json'))
    if updated['spec']['template']['spec']['containers'][0]['image']!=value['image']:
        raise RuntimeError('updated_image_not_confirmed')
    environment={entry['name']:entry.get('value') for entry in updated['spec']['template']['spec']['containers'][0].get('env',[])}
    if any(environment.get(key)!=entry for key,entry in value['environment_update'].items()):
        raise RuntimeError('updated_pipeline_mode_not_confirmed')
    receipt.update(completed=True,revision=updated['status'].get('latestReadyRevisionName'))
    path.write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
