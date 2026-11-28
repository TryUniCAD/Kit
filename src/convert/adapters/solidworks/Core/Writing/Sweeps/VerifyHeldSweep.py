from collections.abc import Mapping
from hashlib import sha256 as CalcSha
from json import loads as LoadJson

from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepPart import SweepPart
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Sweeps.ReadSwHashes import ReadSwHashes
from convert.adapters.solidworks.Core.Writing.Sweeps.SweepMeasPhases import (
    KSwMeasPhases,
)
from interchange.Core.Common import FreezeMapping

# the redacted controlled native run is the authority for these two archive digests
KHeldSweepSha = "d8d698670b21f432e0b6fc98a541d96acf706d9037ad871ec6251fe4be851f70"


# the protected evaluation releases only a pinned digest summary of the original native lifecycles
def ReadHeldSweep(Receipt: Mapping[str, object]) -> dict[str, object]:
    TextValue = Receipt.get("native_report")
    if (
        set(Receipt) != {"native_report"}
        or type(TextValue) is not str
        or len(TextValue) > 200_000
        or CalcSha(TextValue.encode("utf-8")).hexdigest() != KHeldSweepSha
    ):
        raise ValueError("held-out sweep requires authenticated offline evidence")
    Report = ReadMeasMap(LoadJson(TextValue))
    Controls = ReadMeasMap(Report.get("controls"))
    if (
        Report.get("schema") != "kit.sw2026.standard-sweep-heldout-proof.v1"
        or Report.get("oracle_build") != KOraclePart["build"]
        or Report.get("oracle_sha256") != KOraclePart["sha256"]
        or Report.get("native_passed") is not True
        or Report.get("blocked_writer_reads") != 0
        or Report.get("distinct_processes") != 2 * len(KSwMeasPhases) + 2
        or set(Controls) != {"before", "after"}
        or any(ReadMeasMap(Value).get("passed") is not True for Value in Controls.values())
    ):
        raise ValueError("held-out sweep measurement lacks a passing controlled lifecycle")
    return Report


# the neutral writer must reproduce one complete measured original before the report can attest it
def MatchHeldSweep(Report: dict[str, object], Digest: str) -> dict[str, object]:
    Matches = tuple(
        Value
        for Value in ReadMeasRows(Report.get("cases"), 2)
        if ReadSwHashes(Value.get("candidate_sha256"))["original"] == Digest
    )
    if len(Matches) != 1:
        raise ValueError("regenerated sweep has no exact held-out native measurement")
    (CaseValue,) = Matches
    if CaseValue.get("passed") is not True or CaseValue.get("paired_numeric_checks") != 84:
        raise ValueError("held-out sweep measurement lacks its independent comparisons")
    return CaseValue


# historical observations qualify the output digest and contribute no archive fields
def VerifyHeldSweep(
    Receipt: dict[str, object], Candidate: SweepPart
) -> Mapping[str, object]:
    Report = ReadHeldSweep(Receipt)
    Digest = CalcSha(Candidate.BytesValue).hexdigest()
    CaseValue = MatchHeldSweep(Report, Digest)
    Phases = ReadMeasRows(CaseValue.get("phases"), len(KSwMeasPhases))
    if tuple(Value.get("phase") for Value in Phases) != KSwMeasPhases:
        raise ValueError("held-out sweep measurement lacks its two edits and reopens")
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "native_result_sha256": ReadMeasSha(Report.get("native_result_sha256")),
                    "oracle_build": KOraclePart["build"],
                    "phase_record_sha256": tuple(
                        ReadMeasSha(Value.get("receipt_sha256")) for Value in Phases
                    ),
                    "independent_source_sha256": ReadSwHashes(CaseValue.get("source_sha256")),
                    "authority_sha256": KHeldSweepSha,
                }
            )
        }
    )
