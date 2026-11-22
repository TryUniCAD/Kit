from hashlib import sha256 as ShaDigest
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

# the ordinary queue process uses the same guarded archive worker as the disclosure proof
KVisualRoot = FilePath(__file__).resolve().parents[5]


# transport the real source only after verifying its committed hash
def RunVisualCase(RelativeName: str, DigestValue: str) -> CompletedProcess[bytes]:
    SourceValue = (
        KVisualRoot / "re/solidworks/v2026/corpus" / RelativeName
    ).read_bytes()
    assert ShaDigest(SourceValue).hexdigest() == DigestValue
    WorkerValue = KVisualRoot / "re/tooling/sw2026/materials/ProvePartMaterialVisual.py"
    return RunProcess(
        (PythonExec, "-I", "-B", str(WorkerValue), "--worker"),
        input=SourceValue,
        capture_output=True,
        check=False,
        timeout=50,
    )
