from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepPart import SweepPart
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# each sweep output must match its one measured complete payload and actual encoded file identity
def MatchSweepCase(
    Receipt: dict[str, object], Candidate: SweepPart, WrittenAt: int
) -> dict[str, object]:
    Digest = CalcSha(Candidate.BytesValue).hexdigest()
    Cases = ReadMeasRows(Receipt.get("cases"), 2)
    if len(Cases) != 2 or any(
        type(CaseValue.get("slot")) is not int or CaseValue["slot"] != Index
        for Index, CaseValue in enumerate(Cases)
    ):
        raise ValueError("sweep measurement requires two unique ordered case owners")
    Hashes = {ReadMeasSha(CaseValue.get("archive_sha256")) for CaseValue in Cases}
    if len(Hashes) != len(Cases) or Digest not in Hashes:
        raise ValueError(
            "regenerated SOLIDWORKS sweep has no unique exact native measurement"
        )
    CaseValue = next(Value for Value in Cases if Value["archive_sha256"] == Digest)
    HeaderValue = ReadHeaderGraph(
        Candidate.StreamsValue["Contents/Config-0-ModelHeader"],
        Candidate.ConfigValue.VersionValue,
    )
    SelfValue = GetFileRef(HeaderValue.FieldsValue["f38"])
    if (
        type(CaseValue.get("written_at")) is not int
        or WrittenAt != CaseValue["written_at"]
        or HeaderValue.FieldsValue["f70"] != WrittenAt
        or type(CaseValue.get("archive_bytes")) is not int
        or len(Candidate.BytesValue) != CaseValue["archive_bytes"]
        or SelfValue.PathValue != CaseValue.get("locator")
    ):
        raise ValueError(
            "sweep measurement does not match the generated scope or locator"
        )
    return CaseValue
