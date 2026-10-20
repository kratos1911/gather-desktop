"""Build a local model-bearing candidate from a previously verified base image."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from services.inference.artifacts import verify_snapshot
from scripts.prepare_inference_image import digest

ROOT = Path(__file__).resolve().parents[1]


def verify_native_bundle(path, policy):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != policy['native_bundle_sha256']:
        raise ValueError('unreviewed_native_notices')
    value = json.loads(raw)
    if value['unresolved_crates'] or len(value['crates']) != policy['native_crates']:
        raise ValueError('incomplete_native_notices')
    return raw


def image_info(name):
    return json.loads(subprocess.check_output(['docker','image','inspect',name],text=True,timeout=30))[0]


def main():
    if ROOT.drive.upper()!='D:':
        raise ValueError('D_drive_required')
    policy=json.loads((ROOT/'services/inference/release-policy.json').read_text())
    base=image_info(policy['base_image'])
    if base['Id']!=policy['base_image_id']:
        raise ValueError('unreviewed_base_image')
    native=verify_native_bundle(ROOT/'output/native-notices/bundle.json',policy)
    model=verify_snapshot((ROOT/'output/inference-model').resolve())
    build=ROOT/'output/inference-release'
    build.mkdir(exist_ok=True)
    staged=build/'model';staged.mkdir(exist_ok=True)
    for source in model.iterdir():
        destination = staged/source.name
        if not destination.exists() or digest(destination)!=digest(source):
            shutil.copyfile(source,destination)
    verify_snapshot(staged.resolve())
    (build/'native-notices.json').write_bytes(native)
    shutil.copyfile(ROOT/'services/worker/cloud_identity.py',build/'cloud_identity.py')
    (build/'.dockerignore').write_text('**\n!Dockerfile\n!model/*\n!native-notices.json\n!cloud_identity.py\n',encoding='utf-8')
    (build/'Dockerfile').write_text(
        'FROM '+policy['base_image']+'\n'
        'USER 0:0\nRUN mkdir /model && chmod 0555 /model\n'
        'COPY --chown=0:0 --chmod=0444 model/* /model/\n'
        'COPY --chown=0:0 --chmod=0444 native-notices.json /app/native-notices.json\n'
        'COPY --chown=0:0 --chmod=0444 cloud_identity.py /app/services/worker/cloud_identity.py\n'
        'USER 65532:65532\n'
        'ENTRYPOINT ["python", "-m", "services.inference.cloud_startup", "--model", "/model"]\n',encoding='utf-8')
    subprocess.run(['docker','build','--pull=false','--network=none','-t',
                    'gather-inference:release-candidate',str(build)],check=True,timeout=300)
    release=image_info('gather-inference:release-candidate')
    if (image_info(policy['base_image'])['Id']!=base['Id'] or
            release['RootFS']['Layers'][:len(base['RootFS']['Layers'])]!=base['RootFS']['Layers']):
        raise ValueError('base_changed_during_build')
    report={'image':release['Id'],'base_image':base['Id'],'user':release['Config']['User'],
            'cloud_identity_sha256':digest(ROOT/'services/worker/cloud_identity.py'),
            'native_bundle_sha256':policy['native_bundle_sha256'],
            'model_files':len(list(staged.iterdir())),
            'status':'candidate built; real-image smoke and deployment approval required'}
    (ROOT/'tests/inference/results/release-build-20261019.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':
    main()
