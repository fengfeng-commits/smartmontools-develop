"""Read a GitHub credential from the Windows Credential Manager.

This is the same store Git Credential Manager writes to when you sign in with
git on Windows. It is encrypted with DPAPI and only readable as the owning
user; the secret is returned to the caller and never printed or written out.

Windows only. Returns None when nothing usable is stored.
"""

import ctypes
from ctypes import wintypes

CRED_TYPE_GENERIC = 1

GIT_TARGETS = (
    "git:https://github.com",
    "git:https://github.com/",
    "git:https://github.com:443",
)


class _CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def _api():
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi32.CredReadW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(_CREDENTIAL)),
    ]
    advapi32.CredReadW.restype = wintypes.BOOL
    advapi32.CredFree.argtypes = [ctypes.POINTER(_CREDENTIAL)]
    advapi32.CredFree.restype = None
    return advapi32


def read_credential(target):
    """Return {'user', 'secret'} for one target, or None."""
    advapi32 = _api()
    ptr = ctypes.POINTER(_CREDENTIAL)()
    if not advapi32.CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(ptr)):
        return None
    try:
        cred = ptr.contents
        size = cred.CredentialBlobSize
        blob = ctypes.string_at(cred.CredentialBlob, size) if size else b""
        return {"user": cred.UserName,
                "secret": blob.decode("utf-16-le", "ignore").rstrip("\x00")}
    finally:
        advapi32.CredFree(ptr)


def read_token(targets=GIT_TARGETS):
    """Return the first stored GitHub secret found, or None."""
    for t in targets:
        data = read_credential(t)
        if data and data.get("secret"):
            return data["secret"]
    return None
