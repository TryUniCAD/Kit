from pathlib import Path as FilePath

from tests.CliResearch.DirectReader import DirectReader
from tests.CliResearch.NativeVerification.ControlManifest import (
    ControlManifest,
    KAssetPath,
)


# comparisons need actual decoder serialization rather than a hand constructed neutral result
def DecodeControl(TmpPath: FilePath) -> FilePath:
    TargetPath = TmpPath / "Decoded"
    Result = DirectReader(
        TmpPath,
        "FusionReader.py",
        "--manifest",
        str(ControlManifest(TmpPath)),
        "--asset",
        KAssetPath,
        "--output",
        str(TargetPath),
    )
    assert Result.returncode == 0, Result.stderr
    Documents = tuple(TargetPath.rglob("document.json"))
    assert len(Documents) == 1
    return Documents[0]
