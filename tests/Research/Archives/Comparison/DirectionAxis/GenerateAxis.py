from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.Comparison.DirectionAxis.DecodeAxis import DecodeAxis
from tests.Research.Archives.SolidWorksFreshBossTests import KFrontCases, RunPortable


# the comparison requires an independently generated archive with different feature identities
def GenerateAxis(TmpPath: FilePath) -> CadDocument:
    NativePath = TmpPath / "P03DirectionGenerated.SLDPRT"
    CaseValue = {
        **KFrontCases[1],
        "title": NativePath.stem,
        "ids": [57, 71, 91, 92, 93],
        "dimensions_mm": [40.0, 20.0, 10.0],
        "bounds": [[0.0, 0.0, 0.0], [0.04, 0.02, 0.01]],
        "centre_m": [0.02, 0.01, 0.005],
    }
    Result = RunPortable(CaseValue, NativePath)
    assert Result.returncode == 0, Result.stderr + Result.stdout
    Receipt = CastValue(dict[str, object], ReadJson(Result.stdout))
    Payload = NativePath.read_bytes()
    Digest = HashBytes(Payload).hexdigest()
    assert Receipt["archive_sha256"] == Digest
    Document = DecodeAxis(NativePath)
    assert Document.source.format_id == "solidworks.sldprt"
    assert Document.source.sha256 == Digest
    assert NativePath.read_bytes() == Payload
    return Document
