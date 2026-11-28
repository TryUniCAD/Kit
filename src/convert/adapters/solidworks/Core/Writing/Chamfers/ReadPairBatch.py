from convert.adapters.solidworks.Core.Writing.Chamfers.CheckPairPhase import (
    CheckPairPhase,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.CheckPairSlot import (
    CheckPairSlot,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.PairBatch import PairBatch
from convert.adapters.solidworks.Core.Writing.Chamfers.ReadPairReport import (
    ReadPairReport,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha

# the accepted terminal protocol must identify the actual frozen disclosed runner
KPairRunnerSha = "9c331a7e6a8fa43dc483587d0447aeb27e11fe988c715079396a683f87b6a156"


# both disclosed lifecycles and healthy controls must belong to this exact generation manifest
def ReadPairBatch(Receipt: dict[str, object], WrittenAt: int) -> PairBatch:
    if (
        set(Receipt)
        != {"schema", "generation", "native_result", "native_result_sha256"}
        or Receipt.get("schema") != "kit.sw2026.distance-pair-publication.v1"
    ):
        raise ValueError("distance chamfer requires its offline measurement receipt")
    Generation, GenHash = ReadPairReport(Receipt.get("generation"))
    Native, NativeHash = ReadPairReport(Receipt.get("native_result"))
    Destination = Generation.get("destination")
    if (
        Generation.get("schema") != "kit.sw2026.distance-pair-neutral-build.v1"
        or type(Generation.get("written_at")) is not int
        or Generation.get("written_at") != WrittenAt
        or type(Destination) is not str
        or Native.get("schema") != "kit.sw2026.distance-pair-generated-native.v1"
        or Native.get("build") != KOraclePart["build"]
        or Native.get("oracle_sha256") != KOraclePart["sha256"]
        or Native.get("runner_sha256") != KPairRunnerSha
        or Native.get("generation_sha256") != GenHash
        or ReadMeasSha(Receipt.get("native_result_sha256")) != NativeHash
        or Native.get("passed") is not True
        or Native.get("idle_after") is not True
        or Native.get("heldout_writer_acceptance") is not False
        or type(Native.get("distinct_processes")) is not int
        or Native.get("distinct_processes") != 6
    ):
        raise ValueError(
            "distance chamfer measurement does not match its exact oracle batch"
        )
    _ = ReadMeasSha(Native.get("method_sha256"))
    Builds = ReadMeasRows(Generation.get("candidates"), 2)
    Cases = ReadMeasRows(Native.get("candidates"), 2)
    Before, After = ReadMeasRows(Native.get("controls"), 2)
    Controls = (
        CheckPairPhase(Before, "control-before", 0, None),
        CheckPairPhase(After, "control-after", 0, None),
    )
    Phases = tuple(
        CheckPairSlot(CaseValue, BuildValue, Index)
        for Index, (CaseValue, BuildValue) in enumerate(zip(Cases, Builds, strict=True))
    )
    PhaseHashes = {HashValue for SlotHashes in Phases for HashValue in SlotHashes}
    if len(Phases) != 2 or len(PhaseHashes.union(Controls)) != 6:
        raise ValueError("distance chamfer measurement repeats or omits a native phase")
    return PairBatch(Destination, Builds, Cases, Phases, GenHash, NativeHash)
