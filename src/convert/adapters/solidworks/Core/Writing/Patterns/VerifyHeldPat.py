from collections.abc import Mapping
from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.SnapshotReport import (
    SnapshotReport,
)
from interchange.Core.Common import FreezeMapping

# both authorities bind prewriter locked inputs to their independently measured outputs
KPatLockedSha = "abaa363a2722c95166fe33cc668baf4555582b172e663ca67b42b775c9bacfb2"

# the independently repeated second candidate has its own native lifecycle authority
KPatDefaultSha = "f6066ca8a258b2394744632d3062dfdf02bdda3207b84467555f27a0a8a53197"


# only a bound heldout report selects the original platform view arithmetic
def ReadHeldPat(
    Receipt: dict[str, object],
) -> tuple[dict[str, object], str] | None:
    if set(Receipt) != {"native_report"}:
        return None
    Proof, ProofSha = SnapshotReport(ReadMeasMap(Receipt["native_report"]))
    if (
        ProofSha not in (KPatLockedSha, KPatDefaultSha)
        or Proof.get("passed") is not True
    ):
        raise ValueError("linear pattern requires authenticated held-out evidence")
    return Proof, ProofSha


# a native tested pattern qualifies only when the generated container matches exactly
def MatchHeldPat(
    Proof: dict[str, object], ProofSha: str, Payload: bytes
) -> Mapping[str, object]:
    Digest = CalcSha(Payload).hexdigest()
    if ProofSha == KPatLockedSha:
        BuildValue = Proof.get("build")
        Cases = ReadMeasRows(Proof.get("cases"), 2)
        NativeResultSha = ProofSha
    else:
        BuildValue = Proof.get("native_build")
        Cases = (Proof,)
        NativeResultSha = ReadMeasSha(Proof.get("private_receipt_sha256"))
    Matches = tuple(
        CaseValue
        for CaseValue in Cases
        if CaseValue.get("passed") is True
        and CaseValue.get("generated_sha256") == Digest
    )
    if BuildValue != KOraclePart["build"] or len(Matches) != 1:
        raise ValueError("linear pattern has no exact held-out native measurement")
    (CaseValue,) = Matches
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "native_result_sha256": NativeResultSha,
                    "oracle_build": BuildValue,
                    "authority_sha256": ProofSha,
                    "source_lock_sha256": ReadMeasSha(Proof.get("source_lock_sha256")),
                    "qualified_slot": CaseValue["slot"],
                }
            )
        }
    )
