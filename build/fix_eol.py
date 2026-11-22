"""Give shell scripts Unix line endings and Windows launchers Windows ones (the editor on this machine writes CRLF).
    python build/fix_eol.py
"""
import pathlib

CR, LF = bytes([13]), bytes([10])
root = pathlib.Path(__file__).resolve().parent.parent
for f in list(root.glob("build/*.sh")) + list(root.glob("relay/*.sh")):
    b = f.read_bytes(); n = b.replace(CR + LF, LF)
    if n != b:
        f.write_bytes(n); print("LF  ", f.relative_to(root))
for f in root.glob("*.cmd"):
    b = f.read_bytes(); n = b.replace(CR + LF, LF).replace(LF, CR + LF)
    if n != b:
        f.write_bytes(n); print("CRLF", f.relative_to(root))
