"""Windows Credential Manager via OS APIs. No plaintext fallback or key logging."""
import ctypes
from ctypes import wintypes
import os

PROVIDERS = {'gemini', 'nim', 'groq', 'grok'}
class CredentialError(RuntimeError):
    pass

class _Credential(ctypes.Structure):
    _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
                ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
                ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
                ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)), ('Persist', wintypes.DWORD),
                ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p),
                ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]

class WindowsCredentials:
    def __init__(self):
        if os.name != 'nt':
            raise CredentialError('Secure key storage requires Windows. No key was saved.')
        self.api = ctypes.WinDLL('Advapi32.dll', use_last_error=True)
        self.api.CredWriteW.argtypes = [ctypes.POINTER(_Credential), wintypes.DWORD]
        self.api.CredWriteW.restype = wintypes.BOOL
        self.api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(_Credential))]
        self.api.CredReadW.restype = wintypes.BOOL
        self.api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.api.CredDeleteW.restype = wintypes.BOOL
        self.api.CredFree.argtypes = [ctypes.c_void_p]
        self.api.CredFree.restype = None
    @staticmethod
    def target(provider):
        if provider not in PROVIDERS and provider not in {kind+'/'+slot for kind in ('groq','gemini','nim') for slot in ('slot1','slot2','slot3','slot4','slot5')}:
            raise CredentialError('Unknown key provider.')
        return 'JARVIS/provider/' + provider
    def set(self, provider, secret):
        target = self.target(provider)
        if not isinstance(secret, str) or not secret or len(secret.encode('utf-16-le')) > 2560:
            raise CredentialError('Key is empty or too long. No key was saved.')
        raw = secret.encode('utf-16-le')
        blob = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
        c = _Credential(Type=1, TargetName=target, CredentialBlobSize=len(raw),
                        CredentialBlob=blob, Persist=2, UserName='JARVIS')
        try:
            if not self.api.CredWriteW(ctypes.byref(c), 0):
                raise CredentialError('Windows could not save this key. No plaintext fallback was used.')
        finally:
            ctypes.memset(blob, 0, len(raw))
    def status(self, provider):
        """Inspect presence/time only. Never read or decode the secret blob."""
        import datetime
        p = ctypes.POINTER(_Credential)()
        if not self.api.CredReadW(self.target(provider), 1, 0, ctypes.byref(p)):
            if ctypes.get_last_error() == 1168:return {'present':False,'saved_at':None}
            raise CredentialError('Windows could not inspect the saved key.')
        try:
            c=p.contents;stamp=(c.LastWritten.dwHighDateTime<<32)|c.LastWritten.dwLowDateTime
            saved=datetime.datetime.fromtimestamp(stamp/10000000-11644473600,datetime.timezone.utc).astimezone().isoformat(timespec='seconds') if stamp else None
            return {'present':c.CredentialBlobSize>0,'saved_at':saved}
        finally:self.api.CredFree(p)
    def get(self, provider):
        p = ctypes.POINTER(_Credential)()
        if not self.api.CredReadW(self.target(provider), 1, 0, ctypes.byref(p)):
            if ctypes.get_last_error() == 1168:
                return None
            raise CredentialError('Windows could not read the saved key.')
        try:
            return ctypes.string_at(p.contents.CredentialBlob, p.contents.CredentialBlobSize).decode('utf-16-le')
        finally:
            self.api.CredFree(p)
    def delete(self, provider):
        if not self.api.CredDeleteW(self.target(provider), 1, 0) and ctypes.get_last_error() != 1168:
            raise CredentialError('Windows could not remove this key.')
