from re import fullmatch as FullMatch
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# a unique authored case digest must bind to the same generated archive in its build receipt
def MatchMeasCase(Receipt: dict[str, object], Digest: str, ByteCount: int) -> str:
    CaseRows = ReadMeasRows(Receipt.get("cases"), 127)
    BuildRows = ReadMeasRows(Receipt.get("builds"), 127)
    Cases = tuple(
        Entry for Entry in CaseRows if Entry.get("generated_sha256") == Digest
    )
    Builds = tuple(
        Entry for Entry in BuildRows if Entry.get("candidate_sha256") == Digest
    )
    if len(Cases) != 1 or len(Builds) != 1:
        raise ValueError(
            "regenerated SOLIDWORKS part has no unique exact native measurement"
        )
    CaseValue, BuildValue = Cases[0], Builds[0]
    Label = CaseValue.get("role")
    if (
        type(Label) is not str
        or FullMatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", Label) is None
        or sum(Value.get("role") == Label for Value in CaseRows) != 1
        or sum(Value.get("role") == Label for Value in BuildRows) != 1
        or BuildValue.get("role") != Label
        or type(BuildValue.get("bytes")) is not int
        or BuildValue["bytes"] != ByteCount
        or ReadMeasSha(BuildValue.get("build_a_sha256"))
        != ReadMeasSha(BuildValue.get("build_b_sha256"))
        or CaseValue.get("passed") is not True
        or CaseValue.get("archive_locator_absent") is not True
        or CaseValue.get("document_preference_and_unassigned_body_density_match")
        is not True
    ):
        raise ValueError(
            "native measurement has inconsistent candidate ownership or build evidence"
        )
    return Label
