from collections.abc import Mapping
from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping


# the exact complete candidate must identify one and only one measured source slot
def MatchTopCase(
    Proof: dict[str, object], Digest: str, ByteCount: int
) -> tuple[str, dict[str, object]]:
    Cases = tuple(
        (SlotValue, ReadMeasMap(ReadMeasMap(CaseValue).get("build")))
        for SlotValue, CaseValue in ReadMeasMap(Proof.get("cases")).items()
    )
    Matches = tuple(
        (SlotValue, BuildValue)
        for SlotValue, BuildValue in Cases
        if BuildValue.get("bytes") == ByteCount and BuildValue.get("sha256") == Digest
    )
    if len(Matches) != 1:
        raise ValueError("SOLIDWORKS Top box has no exact held-out native measurement")
    return Matches[0]


# the measured edit and reopen hashes belong to the exact generated slot
def ReadTopPhases(Proof: dict[str, object], SlotValue: str) -> tuple[str, str]:
    PhaseRows = ReadMeasRows(Proof.get("phases"), 6)
    Phases = {
        Value.get("name"): Value
        for Value in PhaseRows
        if Value.get("passed") is True and isinstance(Value.get("name"), str)
    }
    EditValue = Phases.get(SlotValue + "Edit")
    ReopenValue = Phases.get(SlotValue + "Reopen")
    if EditValue is None or ReopenValue is None:
        raise ValueError("SOLIDWORKS Top box lacks its measured edit and reopen")
    return ReadMeasSha(EditValue.get("record_sha256")), ReadMeasSha(
        ReopenValue.get("record_sha256")
    )


# publication records the matched archive and measured lifecycle after verifying every logical stream
def MatchTopMeas(
    Proof: dict[str, object], ProofSha: str, Candidate: PartCandidate
) -> Mapping[str, object]:
    Payload = Candidate.BytesValue
    Digest = CalcSha(Payload).hexdigest()
    SlotValue, BuildValue = MatchTopCase(Proof, Digest, len(Payload))
    Expected = ReadMeasMap(BuildValue.get("streams"))
    Actual = {
        NameValue: {"bytes": len(Value), "sha256": CalcSha(Value).hexdigest()}
        for NameValue, Value in Candidate.StreamsValue.items()
    }
    if Actual != Expected:
        raise ValueError("SOLIDWORKS Top box differs from its measured logical streams")
    Edited, Reopened = ReadTopPhases(Proof, SlotValue)
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "native_result_sha256": ReadMeasSha(Proof.get("job_result_sha256")),
                    "oracle_build": Proof["oracle_file_version"],
                    "authority_sha256": ProofSha,
                    "source_lock_sha256": ReadMeasSha(Proof.get("source_lock_sha256")),
                    "qualified_slot": SlotValue,
                    "edit_record_sha256": Edited,
                    "reopen_record_sha256": Reopened,
                }
            )
        }
    )
