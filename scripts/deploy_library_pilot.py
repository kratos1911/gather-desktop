"""Preview by default. Apply only after explicit approval of this Gather plan.

Passwords go from current-user DPAPI through stdin to two named Gather secrets;
they are never arguments, files, receipts or desktop assets.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from services.worker.local_credentials import load

ROOT=Path(__file__).resolve().parents[1]
PROJECT='gather-development-511211'
ACCOUNT='kpanigrahi5602@gmail.com'
SERVICE='gather-library-pilot'
CALLER='gather-pilot-caller@'+PROJECT+'.iam.gserviceaccount.com'
SECRETS={'gather_admission':'gather-library-admission','gather_worker':'gather-library-worker'}


def plan():
    artifact=json.loads((ROOT/'output/library-image/verification.json').read_text())
    image=artifact['image']
    if image!='sha256:522826fd030d34807e17c2073c1b23d8376a30d215d936f738e74f83a4cc3724' or artifact['linux_checks']!=37:
        raise ValueError('verified_api_image_mismatch')
    return {'project':PROJECT,'account':ACCOUNT,'region':'asia-south1','service':SERVICE,
        'image':'asia-south1-docker.pkg.dev/'+PROJECT+'/gather-pilot-images/library@'+image,
        'cpu':1,'memory':'512Mi','minimum':0,'maximum':1,'concurrency':4,
        'application_admission':1,'model_attempts_per_instance':3,
        'runtime_identity':CALLER,'secrets':list(SECRETS.values()),
        'authentication':'Supabase verification and fixed two-account allowlist on every application operation',
        'public_https_entrypoint':True,'permanent_warming':False,
        'budget':'Existing INR500 aggregate pilot allowance; alerts do not enforce a hard cap'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    value=plan()
    if not args.apply: print(json.dumps(value,indent=2)); return
    executable=shutil.which('gcloud.cmd')
    if executable is None: raise ValueError('gcloud_unavailable')
    def call(*command,data=None,missing=False):
        result=subprocess.run([executable,*command,'--project='+PROJECT,'--account='+ACCOUNT,'--quiet'],
            input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=240)
        if result.returncode and not missing: raise RuntimeError('cloud_step_failed_'+str(result.returncode))
        return result
    # Refuse accidental updates to an existing service or secret namespace.
    if call('run','services','describe',SERVICE,'--region=asia-south1',missing=True).returncode==0:
        raise ValueError('library_service_already_exists_review_before_update')
    for name in SECRETS.values():
        if call('secrets','describe',name,missing=True).returncode==0:
            raise ValueError('library_secret_already_exists_review_before_update')
    passwords=load()
    public=json.loads((ROOT/'output/supabase/pilot-public.json').read_text(encoding='utf-8-sig'))
    if public['project_ref']!='fatolholcjxpwocnpzws' or not public['publishable_key'].startswith('sb_publishable_'):
        raise ValueError('public_configuration_mismatch')
    receipt={'project':PROJECT,'service':SERVICE,'steps':[]}
    path=ROOT/'output/library-image/deployment.json'
    def saved(step):
        receipt['steps'].append(step)
        path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        print(step,flush=True)
    call('services','enable','secretmanager.googleapis.com'); saved('secret_api_enabled')
    for role,name in SECRETS.items():
        call('secrets','create',name,'--replication-policy=user-managed','--locations=asia-south1')
        saved(name+'_created')
        call('secrets','versions','add',name,'--data-file=-',data=passwords[role].encode('utf-8'))
        saved(name+'_version_created')
        call('secrets','add-iam-policy-binding',name,'--member=serviceAccount:'+CALLER,'--role=roles/secretmanager.secretAccessor')
        saved(name+'_runtime_access_granted')
    passwords.clear()
    mounts=','.join('/secrets/'+role+'/password='+name+':1' for role,name in SECRETS.items())
    call('run','deploy',SERVICE,'--image='+value['image'],'--region=asia-south1','--platform=managed',
        '--service-account='+CALLER,'--cpu=1','--memory=512Mi','--concurrency=4','--min=0','--max=1',
        '--port=8080','--timeout=30s','--execution-environment=gen2','--no-cpu-throttling','--no-cpu-boost',
        '--allow-unauthenticated','--set-secrets='+mounts,
        '--set-env-vars=GATHER_PROJECT='+PROJECT+',GATHER_PUBLISHABLE_KEY='+public['publishable_key'])
    saved('library_service_deployed')


if __name__=='__main__':
    try: main()
    except Exception as error:
        raise SystemExit(type(error).__name__+': library deployment stopped; inspect safe steps, never retry automatically.') from None
