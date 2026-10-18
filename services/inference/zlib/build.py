"""Run inside the isolated Linux toolchain; output stays in /work on D:."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

WORK = Path('/work')
REPO = Path('/repo')
VERSION = '1:1.3.dfsg+really1.3.1-1+gather1'
SOURCES = {
    'source.dsc': 'ede2791e29c1d3b422f9208bdd7edf040c20445ea1e7453a72037576e64fa197',
    'zlib_1.3.dfsg+really1.3.1.orig.tar.gz': '60dd315c07f616887caa029408308a018ace66e3d142726a97db164b3b8f69fb',
    'zlib_1.3.dfsg+really1.3.1-1.debian.tar.xz': '9ed525955ce9fb0c1b39be8ff98f73450dbfc6305a9a27e6149c8972d38a0a9e',
}


def run(args, cwd, expected=0, env=None):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env, timeout=600)
    with (WORK / 'build.log').open('a') as log:
        log.write('COMMAND '+repr(args)+'\n'+result.stdout+'\n')
    if result.returncode != expected:
        raise RuntimeError(f'{args[0]} returned {result.returncode}, expected {expected}: {result.stdout[-2500:]}')
    return result.stdout


def main():
    for name, sha in SOURCES.items():
        if hashlib.sha256((WORK/name).read_bytes()).hexdigest() != sha:
            raise ValueError('Unreviewed source archive')
    build = Path(tempfile.mkdtemp(prefix='build-', dir=WORK))
    source = build / 'source'
    run(['dpkg-source', '--no-check', '-x', str(WORK/'source.dsc'), str(source)], build)
    # An unpatched control must exhibit the stale input state, not just compile.
    run(['./configure', '--static'], source)
    run(['make', '-j1'], source)
    test = str(REPO/'tests/inference/zlib_error_state.c')
    run(['gcc', '-I.', test, './libz.a', '-o', 'error-state'], source)
    control = run(['./error-state'], source, expected=42)
    run(['make', 'distclean'], source)
    patch = REPO/'services/inference/zlib/CVE-2026-85091.patch'
    run(['patch', '--fuzz=0', '-p1', '-i', str(patch)], source)
    # Keep the applied source patch in Debian's source package metadata too.
    (source/'debian/patches').mkdir(exist_ok=True)
    shutil.copyfile(patch, source/'debian/patches/gather-error-state.patch')
    changelog = source/'debian/changelog'
    old = changelog.read_text()
    # Attribute this local change to the configured project identity, not Debian.
    maintainer = os.environ['GATHER_PACKAGE_MAINTAINER']
    if '\n' in maintainer or '\r' in maintainer or '<' not in maintainer or not maintainer.endswith('>'):
        raise ValueError('Explicit valid local package maintainer required')
    signature = f' -- {maintainer}  Sun, 18 Oct 2026 00:00:00 +0000'
    changelog.write_text(f'zlib ({VERSION}) unstable; urgency=high\n\n'
                        '  * Local Gather backport of upstream df84af25 for CVE-2026-85091.\n'
                        '    This is not an official Debian update.\n\n'+signature+'\n\n'+old)
    env = dict(os.environ, DEB_BUILD_PROFILES='nobiarch', DEB_BUILD_OPTIONS='parallel=1',
               SOURCE_DATE_EPOCH='1792281600')
    run(['dpkg-buildpackage', '-b', '-us', '-uc', '-P', 'nobiarch'], source, env=env)
    run(['gcc', '-I.', test, './libz.a', '-o', 'error-state'], source)
    fixed = run(['./error-state'], source)
    run(['gcc', '-I.', test, '-L.', '-lz', '-o', str(WORK/'error-state-dynamic')], source)
    package = next(build.glob('zlib1g_*_amd64.deb'))
    target = WORK/'zlib1g-gather1.deb'
    shutil.copyfile(package, target)
    evidence = {'version': VERSION, 'source_hashes': SOURCES,
                'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
                'package_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'control_exit': 42, 'patched_exit': 0,
                'control_output': control.strip(), 'patched_output': fixed.strip(),
                'standard_tests': ['zlib test', 'zlib shared test', 'zlib 64-bit test'],
                'package': str(package), 'source': str(source),
                'provenance': 'Debian HTTPS descriptor hashes checked; OpenPGP signature not verified',
                'toolchain': run(['dpkg-query', '-W', 'gcc', 'libc6-dev', 'dpkg-dev', 'debhelper'], build)}
    (WORK/'evidence.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
