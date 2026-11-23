from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows


# the generated whole archive and typed self identity must match its one measured case
def MatchAngleCase(
    Trial: dict[str, object], Candidate: PartCandidate, WrittenAt: int
) -> tuple[int, str]:
    Digest = CalcSha(Candidate.BytesValue).hexdigest()
    Cases = ReadMeasRows(Trial.get("cases"), 2)
    Matches = tuple(
        (Index, RowValue)
        for Index, RowValue in enumerate(Cases)
        if RowValue.get("archive_sha256") == Digest
    )
    if len(Matches) != 1:
        raise ValueError(
            "regenerated angle-distance chamfer has no exact native measurement"
        )
    ((SlotValue, CaseValue),) = Matches
    Proof = ReadMeasMap(CaseValue.get("writer_proof"))
    Header = ReadHeaderGraph(
        Candidate.StreamsValue["Contents/Config-0-ModelHeader"],
        Candidate.ConfigValue.VersionValue,
    ).FieldsValue
    Feature = RequireNative(Candidate.ResolvedValue.RootsValue[-1], "Chamfer_c")
    if (
        Header.get("f70") != WrittenAt
        or GetFileRef(Header.get("f38")).PathValue != CaseValue.get("locator")
        or len(Candidate.BytesValue) != Proof.get("archive_bytes")
        or Feature.FieldsValue.get("f8c0") != 1
    ):
        raise ValueError("angle-distance chamfer measurement has a foreign scope")
    return SlotValue, Digest
