from typing import cast as CastValue

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.SnapshotReport import (
    SnapshotReport,
)

# the original held out lifecycle has its own native evidence schema
KTopMeasSchema = "kit.sw2026.attached-top-box-heldout-evaluation.v1"

# only the exact healthy prewriter locked batch can authorize measured top box output
KTopReportSha = "b50eb4668453ab4698f9bed0289809ba347b43a78c580a0646b8c3e0f3b6be38"


# existing part families retain their dispatch unless the supplied report identifies the top box cohort
def HasTopMeas(OptionsValue: WriteOptions | None) -> bool:
    if not isinstance(OptionsValue, WriteOptions):
        return False
    Envelope = OptionsValue.values.get(KPartMeasureOpt)
    if type(Envelope) is not dict:
        return False
    Receipt = CastValue(dict[str, object], Envelope).get("receipt")
    return (
        type(Receipt) is dict
        and CastValue(dict[str, object], Receipt).get("schema") == KTopMeasSchema
    )


# the authenticated snapshot supplies only acceptance evidence and cannot supply model values
def ReadTopMeas(Receipt: dict[str, object]) -> tuple[dict[str, object], str]:
    Proof, ProofSha = SnapshotReport(Receipt)
    if (
        ProofSha != KTopReportSha
        or Proof.get("schema") != KTopMeasSchema
        or Proof.get("passed") is not True
        or Proof.get("controls_healthy") is not True
        or Proof.get("oracle_file_version") != KOraclePart["build"]
        or Proof.get("oracle_sha256") != KOraclePart["sha256"]
    ):
        raise ValueError("SOLIDWORKS Top box requires authenticated held-out evidence")
    return Proof, ProofSha
