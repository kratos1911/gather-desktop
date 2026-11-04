"""Preview by default; approved Gather-only cache secrets and existing API rollout."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from services.worker.local_query_cache import load

ROOT=Path(__file__).resolve().parents[1]
PROJECT='gather-development-511211'
ACCOUNT='kpanigrahi5602@gmail.com'
REGION='asia-south1'
SERVICE='gather-library-pilot'
RUNTIME='gather-pilot-caller@'+PROJECT+'.iam.gserviceaccount.com'
CACHE_ENDPOINT='https://relaxing-goshawk-225370.upstash.io'
PREVIOUS='sha256:2e33313413ae31a0ae6c28767f6ae066410bc5243075767056e84d516d14aae3'
SECRETS={'token':('gather-upstash-rest-token','/secrets/gather_upstash/token'),
         'key':('gather-query-cache-key','/secrets/gather_query_cache/key')}


def plan(correct=False):
    proof=json.loads((ROOT/('output/upstash-cache/corrected-image-verification.json' if correct else 'output/upstash-cache/image-verification.json')).read_text())
    expected=('sha256:8cff0f17326cafd02c9f3bd51272a2ece8278c5272aca4b4ec513a64117e6ccb' if correct else
              'sha256:ab41ddcdcb165f0edfd58d1a6d539df2ff669be4a55350f07b60816b7353bf6b')
    if proof.get('passed') is not True or proof['image']!=expected:
        raise ValueError('unverified_cache_image')
    return dict(project=PROJECT,account=ACCOUNT,region=REGION,service=SERVICE,
        image=REGION+'-docker.pkg.dev/'+PROJECT+'/gather-pilot-images/library@'+proof['image'],
        cache_endpoint=CACHE_ENDPOINT,cache_ttl_seconds=600,cache_operation_seconds=1 if correct else .5,
        secrets=[value[0] for value in SECRETS.values()],secret_reader=RUNTIME,
        cpu=1,memory='2Gi',minimum=0,maximum=1,
        budget='Existing INR500 allowance; Upstash remains Free',model_changes=False,
        new_secret_or_iam_changes=not correct)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--correct',action='store_true',help='Cache deadline/diagnostic image only; retain existing secrets, IAM and environment.')
    args=parser.parse_args();value=plan(args.correct)
    if not args.apply:
        print(json.dumps(value,indent=2));return
    executable=shutil.which('gcloud.cmd')
    if executable is None:raise ValueError('gcloud_unavailable')
    def call(*command,secret=None):
        result=subprocess.run([executable,*command,'--project='+PROJECT,'--account='+ACCOUNT,'--quiet'],
            input=secret,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=240)
        if result.returncode:raise RuntimeError('cache_cloud_step_failed')
        return result.stdout
    def describe():
        return json.loads(call('run','services','describe',SERVICE,'--region='+REGION,'--format=json'))
    def bound(service):
        template=service['spec']['template'];spec=template['spec'];container=spec['containers'][0]
        annotations={**template['metadata'].get('annotations',{}),**service['metadata'].get('annotations',{})}
        if (spec['serviceAccountName']!=RUNTIME or container['resources']['limits']!={'cpu':'1','memory':'2Gi'}
                or not any(annotations.get(k)=='1' for k in ('autoscaling.knative.dev/maxScale','run.googleapis.com/maxScale'))
                or any(annotations.get(k) not in (None,'0') for k in ('autoscaling.knative.dev/minScale','run.googleapis.com/minScale'))):
            raise ValueError('gather_configuration_changed')
        return spec,container
    current=describe();old_spec,old=bound(current)
    expected_previous=('sha256:ab41ddcdcb165f0edfd58d1a6d539df2ff669be4a55350f07b60816b7353bf6b' if args.correct else PREVIOUS)
    if not old['image'].endswith('@'+expected_previous):raise ValueError('gather_revision_changed_review_required')
    path=ROOT/('output/upstash-cache/corrected-deployment.json' if args.correct else 'output/upstash-cache/deployment.json')
    receipt=dict(value,completed=False,secrets_prepared=[],previous_revision=current['status']['latestReadyRevisionName'])
    path.write_text(json.dumps(receipt,indent=2))
    if args.correct:
        before={row['name']:row.get('value') for row in old.get('env',[])}
        if before.get('GATHER_QUERY_CACHE')!='1' or before.get('GATHER_UPSTASH_URL')!=CACHE_ENDPOINT:
            raise ValueError('existing_cache_configuration_changed')
        call('run','services','update',SERVICE,'--region='+REGION,'--image='+value['image'])
        updated=describe();new_spec,new=bound(updated)
        if (new['image']!=value['image'] or new.get('env',[])!=old.get('env',[])
                or new_spec.get('volumes',[])!=old_spec.get('volumes',[])
                or new.get('volumeMounts',[])!=old.get('volumeMounts',[])):
            raise RuntimeError('corrective_configuration_not_verified')
        receipt.update(completed=True,revision=updated['status']['latestReadyRevisionName'])
        path.write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2));return
    existing={row['name'].rsplit('/',1)[-1]:row for row in json.loads(call('secrets','list','--format=json'))}
    values=load()
    # Existing secrets are accepted only for recovery of this exact labelled setup.
    for field,(name,_mount) in SECRETS.items():
        raw=values[field].encode('ascii')
        if name in existing:
            meta=existing[name]
            if meta.get('labels',{}).get('purpose')!='gather-query-cache-v1':
                raise ValueError('existing_secret_requires_review')
            if call('secrets','versions','access','1','--secret='+name)!=raw:
                raise ValueError('existing_secret_value_changed')
        else:
            call('secrets','create',name,'--replication-policy=user-managed','--locations='+REGION,
                 '--labels=app=gather,purpose=gather-query-cache-v1','--data-file=-',secret=raw)
        call('secrets','add-iam-policy-binding',name,'--member=serviceAccount:'+RUNTIME,
             '--role=roles/secretmanager.secretAccessor')
        receipt['secrets_prepared'].append(name);path.write_text(json.dumps(receipt,indent=2))
    mounts=','.join(mount+'='+name+':1' for name,mount in SECRETS.values())
    call('run','services','update',SERVICE,'--region='+REGION,'--image='+value['image'],
         '--update-secrets='+mounts,'--update-env-vars=GATHER_QUERY_CACHE=1,GATHER_UPSTASH_URL='+value['cache_endpoint'])
    updated=describe();new_spec,new=bound(updated)
    env={row['name']:row.get('value') for row in new.get('env',[])}
    if new['image']!=value['image'] or env.get('GATHER_QUERY_CACHE')!='1' or env.get('GATHER_UPSTASH_URL')!=value['cache_endpoint']:
        raise RuntimeError('cache_update_not_verified')
    if any(row not in new.get('env',[]) for row in old.get('env',[])):
        raise RuntimeError('existing_environment_changed')
    if any(row not in new_spec.get('volumes',[]) for row in old_spec.get('volumes',[])):
        raise RuntimeError('existing_secret_mount_changed')
    if any(row not in new.get('volumeMounts',[]) for row in old.get('volumeMounts',[])):
        raise RuntimeError('existing_secret_mount_changed')
    volumes={row['name']:row.get('secret',{}) for row in new_spec.get('volumes',[])}
    for name,mount in SECRETS.values():
        parent,filename=mount.rsplit('/',1)
        links=[row for row in new.get('volumeMounts',[]) if row['mountPath']==parent]
        if len(links)!=1:
            raise RuntimeError('cache_secret_mount_not_verified')
        secret=volumes.get(links[0]['name'],{})
        if secret.get('secretName')!=name or not any(
                item.get('key')=='1' and item.get('path')==filename for item in secret.get('items',[])):
            raise RuntimeError('cache_secret_mount_not_verified')
    receipt.update(completed=True,revision=updated['status']['latestReadyRevisionName'])
    path.write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Cache rollout stopped. Inspect the safe receipt; do not retry automatically. No secrets printed.') from None
