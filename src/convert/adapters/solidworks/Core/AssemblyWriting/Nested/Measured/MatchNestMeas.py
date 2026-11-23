from hashlib import sha256 as CalcSha
from json import dumps as DumpJson
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.Measured.NestMeasure import (
    NestMeasure,
)


# the native evidence must bind every computed member at its actual encoded locator
def MatchNestMeas(
    Evidence: NestMeasure,
    FilesValue: tuple[PureWindowsPath, ...],
    Candidates: tuple[tuple[PureWindowsPath, TargetDocument], ...],
) -> None:
    if len(FilesValue) != len(Candidates) or len(Candidates) != Evidence.MemberCount:
        raise ValueError("nested measurement has a different complete member count")
    Manifest: dict[str, dict[str, str | int]] = {}
    for PathValue, (LogicalPath, Candidate) in zip(FilesValue, Candidates, strict=True):
        if str(PathValue) != str(LogicalPath) or any(
            ReadFileKey(RequireNode(Record.FieldsValue.get("f38"), "moExtObject_c"))[1]
            != str(PathValue)
            for Record in (Candidate.HeaderValue, Candidate.TopHeader)
        ):
            raise ValueError("nested candidate header has a different measured locator")
        Manifest[PathValue.name] = {
            "bytes": len(Candidate.BytesValue),
            "sha256": CalcSha(Candidate.BytesValue).hexdigest(),
        }
    Encoded = DumpJson(
        Manifest, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if CalcSha(Encoded).hexdigest() != Evidence.ManifestSha:
        raise ValueError(
            "nested assembly measurement does not match the exact generated bundle"
        )
