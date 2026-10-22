"""Windows operator-only encrypted pilot credentials; never desktop distribution."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path

from services.worker.database_transport import DatabaseConfig
from services.worker.service_transport import strict_json

ROOT = Path(__file__).resolve().parents[2]
PROJECT = 'fatolholcjxpwocnpzws'
HOST = 'aws-0-ap-southeast-2.pooler.supabase.com'
ROLES = ('gather_admission','gather_worker')
STORE = ROOT/('output/credentials/supabase-'+PROJECT+'.dpapi')
CERT = ROOT/'output/supabase-cli/prod-ca-2021.crt'
MAX_BYTES = 16384


class CredentialError(Exception):
    pass


def validate(values):
    if (not isinstance(values,dict) or set(values)!=set(ROLES)
            or any(not isinstance(p,str) or not 24<=len(p)<=1024 or '\x00' in p for p in values.values())
            or values[ROLES[0]]==values[ROLES[1]]):
        raise CredentialError('invalid_credentials')


def dpapi(raw, *, decrypt=False):
    if os.name!='nt' or type(raw) is not bytes or not 0<len(raw)<=MAX_BYTES:
        raise CredentialError('windows_protection_unavailable')
    class Blob(ctypes.Structure):
        _fields_ = [('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
    def blob(value):
        buffer = ctypes.create_string_buffer(value)
        return Blob(len(value),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte))),buffer
    source, source_buffer = blob(raw)
    entropy, entropy_buffer = blob(('Gather local pilot credentials v1:'+PROJECT).encode())
    result = Blob()
    crypt = ctypes.WinDLL('crypt32',use_last_error=True)
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.POINTER(Blob),
                         ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    try:
        # UI forbidden; machine-wide decryption is deliberately never enabled.
        if not function(ctypes.byref(source),None,ctypes.byref(entropy),None,None,1,ctypes.byref(result)):
            raise CredentialError('windows_protection_failed')
        if not 0<result.size<=MAX_BYTES:
            raise CredentialError('invalid_protected_data')
        return ctypes.string_at(result.data,result.size)
    finally:
        ctypes.memset(source_buffer,0,len(source_buffer))
        if result.data:
            ctypes.memset(result.data,0,result.size)
            kernel.LocalFree(result.data)


def save(values):
    validate(values)
    raw = json.dumps({'project':PROJECT,'version':1,'passwords':values},allow_nan=False).encode()
    encrypted = dpapi(raw)
    if dpapi(encrypted,decrypt=True)!=raw:
        raise CredentialError('local_decryption_failed')
    STORE.parent.mkdir(parents=True,exist_ok=True)
    # Never silently replace credentials or follow an existing file/symlink.
    with STORE.open('xb') as stream:
        stream.write(encrypted)


def load():
    try:
        if STORE.is_symlink() or not STORE.is_file():
            raise ValueError()
        with STORE.open('rb') as stream:
            raw = stream.read(MAX_BYTES+1)
        value = strict_json(dpapi(raw,decrypt=True))
        if (set(value)!={'project','version','passwords'} or value['project']!=PROJECT
                or type(value['version']) is not int or value['version']!=1):
            raise ValueError()
        validate(value['passwords'])
        return value['passwords']
    except Exception:
        raise CredentialError('local_credentials_unavailable') from None


def database_config(role):
    if role not in ROLES:
        raise CredentialError('invalid_credential_role')
    return DatabaseConfig(HOST,5432,role+'.'+PROJECT,load()[role],root_certificate=str(CERT))
