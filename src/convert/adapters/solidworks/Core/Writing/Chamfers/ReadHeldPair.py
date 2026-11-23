from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.SnapshotReport import (
    SnapshotReport,
)

# the redacted protected report binds two candidates and their native evaluation
KHeldPairReportSha = "00ebeab7479f9a9cc6468d4f91412e0a15bb162c65c4fdf32536d23b21857c36"


# only the authenticated prewriter cohort uses the original platform view arithmetic
def ReadHeldPair(Receipt: dict[str, object]) -> dict[str, object] | None:
    if set(Receipt) != {"native_report"}:
        return None
    Proof, ProofSha = SnapshotReport(ReadMeasMap(Receipt["native_report"]))
    if (
        ProofSha != KHeldPairReportSha
        or Proof.get("schema") != "kit.sw2026.distance-pair-generated-native.v1"
        or Proof.get("oracle_sha256") != KOraclePart["sha256"]
        or Proof.get("build") != KOraclePart["build"]
        or Proof.get("heldout_writer_acceptance") is not True
        or Proof.get("passed") is not True
        or Proof.get("distinct_processes") != 6
    ):
        raise ValueError("distance chamfer requires authenticated held-out evidence")
    return Proof
