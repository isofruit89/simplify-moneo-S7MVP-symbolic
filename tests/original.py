"""Loads the original script TIAExportv2.py directly from the old exe (PyInstaller archive).

This allows calling the original functions without console/dialogs and comparing
them with ``core.py``. Requires Python 3.12 (same version as the exe).
"""
import builtins
import marshal
import os
import struct
import zlib
from pathlib import Path

# Old exe used as reference. Override with the environment variable TIA2MONEO_LEGACY_EXE.
DEFAULT_EXE = Path(
    os.environ.get("TIA2MONEO_LEGACY_EXE")
    or Path(__file__).resolve().parents[1] / "legacy" / "TIAExportv2.exe"
)
MAGIC = b"MEI\x0c\x0b\x0a\x0b\x0e"


def load_code(exe_path=DEFAULT_EXE, entry="TIAExportv2"):
    data = Path(exe_path).read_bytes()
    i = data.rfind(MAGIC)
    _, length, toc, toc_len, _pyver, _lib = struct.unpack("!8sIIII64s", data[i:i + 88])
    start = len(data) - length
    pos, end = start + toc, start + toc + toc_len
    while pos < end:
        size, epos, csize, _usize, flag, _typ = struct.unpack("!IIIIBc", data[pos:pos + 18])
        name = data[pos + 18:pos + size].rstrip(b"\0").decode()
        pos += size
        if name == entry:
            raw = data[start + epos:start + epos + csize]
            return marshal.loads(zlib.decompress(raw) if flag else raw)
    raise LookupError(f"{entry} not found in {exe_path}")


def load_module(exe_path=DEFAULT_EXE):
    """Executes the original module without running its __main__ part (dialogs)."""
    code = load_code(exe_path)
    fake_builtins = dict(vars(builtins))
    fake_builtins["input"] = lambda *a, **k: ""
    fake_builtins["print"] = lambda *a, **k: None
    ns = {"__name__": "tiaexport_original", "__builtins__": fake_builtins}
    exec(code, ns)
    return ns
