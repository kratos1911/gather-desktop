"""Build-time only: install exact reviewed wheels without network or pip."""
import hashlib
from importlib import metadata
from pathlib import Path, PurePosixPath
import shutil
import stat
import sysconfig
import zipfile

PINS = (
    ('Pillow', '13.0.0', 'pillow-13.0.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl',
     '42d63be3af4f9b951b199b0a9d23365d37ab14687e6d77b74940432c8515c4ca',
     ('PIL', 'pillow.libs', 'pillow-13.0.0.dist-info'), ()),
    ('pyasn1', '0.6.5', 'pyasn1-0.6.5-py3-none-any.whl',
     '4017b0fce125096b8573b39c989fdb1a4b19cf761e683398184550fea0e66587',
     ('pyasn1', 'pyasn1-0.6.5.dist-info'), ('pyasn1', 'pyasn1-0.6.4.dist-info')),
    ('setuptools', '84.1.0', 'setuptools-84.1.0-py3-none-any.whl',
     '5231689c6ac8156cd155cfb98c3fd6fb252c3e7e9bd3d78b64d3c55f132624c9',
     ('setuptools', '_distutils_hack', 'distutils-precedence.pth', 'setuptools-84.1.0.dist-info'),
     ('setuptools', '_distutils_hack', 'distutils-precedence.pth', 'setuptools-84.0.0.dist-info')),
)


def main():
    target = Path(sysconfig.get_path('purelib')).resolve()
    if str(target) != '/usr/local/lib/python3.12/site-packages':
        raise ValueError('unexpected_build_runtime')
    # Fence old versions before modifying this disposable image layer.
    if metadata.version('pyasn1') != '0.6.4' or metadata.version('setuptools') != '84.0.0':
        raise ValueError('security_overlay_base_changed')
    for package, version, filename, digest, roots, old in PINS:
        wheel = Path('/app/ocr-wheels') / filename
        if not wheel.is_file() or wheel.stat().st_size > 20*1024*1024 or hashlib.sha256(wheel.read_bytes()).hexdigest() != digest:
            raise ValueError('ocr_wheel_integrity')
        with zipfile.ZipFile(wheel) as archive:
            for entry in archive.infolist():
                name = PurePosixPath(entry.filename)
                if (name.is_absolute() or '..' in name.parts or not name.parts or name.parts[0] not in roots
                        or stat.S_ISLNK(entry.external_attr >> 16)):
                    raise ValueError('ocr_wheel_path')
            for name in old:
                path = target / name
                if path.parent != target or path.is_symlink():
                    raise ValueError('unexpected_overlay_path')
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.is_file():
                    path.unlink()
            archive.extractall(target)
        wheel.unlink()
        if metadata.version(package) != version:
            raise ValueError('ocr_install_identity')


if __name__ == '__main__':
    main()
