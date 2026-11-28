from hashlib import sha256 as CalcSha
from typing import Mapping as TypeMap

from interchange.Core.Common import FreezeMapping
from convert.adapters.Fusion.Measurement.CheckFuseCube import CheckDriver, CheckFuseCube
from convert.adapters.Fusion.Measurement.CheckFuseEdit import CheckFuseEdit
from convert.adapters.Fusion.Measurement.CheckFuseState import (
    IsSameState,
    ReadFuseState,
)
from convert.adapters.Fusion.Measurement.FusionMeasOpt import KFusionMeasOpt
from convert.adapters.Fusion.Measurement.IsFuseGeom import IsFuseGeom
from convert.adapters.Fusion.Measurement.ReadFuseMeas import (
    ReadMeasList,
    ReadMeasMap,
    ReadMeasPid,
    ReadMeasSha,
)
from convert.adapters.Fusion.Projection.NativeIndex import MakeIndex
from convert.adapters.Fusion.Projection.NativeProfile import NativeProfile
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


# each stage must have opened and rebuilt the same healthy model and closed its documents
def ReadMeasStage(Value: object) -> dict[str, object]:
    Stage = ReadMeasMap(Value)
    Remaining = Stage.get("documents_after")
    if (
        Stage.get("application") != "fusion"
        or Stage.get("status") != "measured"
        or Stage.get("load_errors") != []
        or type(Remaining) is not int
        or Remaining != 0
        or not IsSameState(ReadFuseState(Stage.get("opened")), Stage.get("rebuilt"))
    ):
        raise ValueError("Fusion measurement stage did not open and rebuild cleanly")
    return Stage


# bracketing controls and the candidate must share a build while using distinct processes
def ReadMeasRun(
    Receipt: dict[str, object],
) -> tuple[dict[str, object], dict[str, object], frozenset[int]]:
    Controls = ReadMeasMap(Receipt.get("controls"))
    Before = ReadMeasStage(Controls.get("before"))
    After = ReadMeasStage(Controls.get("after"))
    Candidate = ReadMeasStage(Receipt.get("candidate"))
    Build = Candidate.get("build")
    Processes = frozenset(
        ReadMeasPid(Stage.get("pid")) for Stage in (Before, Candidate, After)
    )
    if (
        not isinstance(Build, str)
        or not Build.strip()
        or Before.get("build") != Build
        or After.get("build") != Build
        or len(Processes) != 3
        or ReadMeasSha(Before.get("source_sha256")) != After.get("source_sha256")
        or not IsSameState(ReadFuseState(Before["rebuilt"]), After["rebuilt"])
    ):
        raise ValueError(
            "Fusion measurement requires equivalent fresh-process controls"
        )
    return Candidate, ReadFuseState(Before["rebuilt"]), Processes


# only measurements bound to the entire emitted archive can attest native usability
def MatchFuseMeas(Value: object, Payload: bytes) -> TypeMap[str, object]:
    Receipt = ReadMeasMap(Value)
    Digest = CalcSha(Payload).hexdigest()
    Schema = Receipt.get("schema")
    if (
        type(Schema) is not int
        or Schema != 1
        or Receipt.get("application") != "fusion"
        or Receipt.get("role") not in ("reconstruction", "edited")
        or Receipt.get("candidate_sha256") != Digest
    ):
        raise ValueError(
            "Fusion measurement does not match the exact generated archive"
        )
    Candidate, Control, Processes = ReadMeasRun(Receipt)
    Rebuilt = ReadFuseState(Candidate["rebuilt"])
    Model = ReadDocument(Payload)
    SpecValue = NativeProfile(MakeIndex(Model), Model)
    if (
        SpecValue.ProfileKind != "cuboid"
        or not SpecValue.ConstrainRectangle
        or SpecValue.TaperDegrees
    ):
        raise ValueError("Fusion measurement requires the constrained cuboid profile")
    if (
        Candidate.get("source_sha256") != Digest
        or Rebuilt["features"] != Control["features"]
        or Rebuilt["sketches"] != Control["sketches"]
        or not IsFuseGeom(Rebuilt["bodies"], Control["bodies"])
    ):
        raise ValueError("Fusion measurement does not match the independent control")
    CheckFuseCube(Rebuilt, SpecValue, SpecValue.LengthMm)
    CheckDriver(Rebuilt, SpecValue, SpecValue.LengthMm)
    Edits = ReadMeasList(Candidate.get("edits"))
    if len(Edits) != 1:
        raise ValueError("Fusion measurement requires an exact cuboid driving edit")
    EditValue = ReadMeasMap(Edits[0])
    CheckFuseEdit(EditValue, Rebuilt, SpecValue)
    if ReadMeasPid(EditValue.get("reopen_pid")) in Processes or ReadMeasSha(
        EditValue.get("saved_sha256")
    ) == ReadMeasSha(EditValue.get("restored_sha256")):
        raise ValueError(
            "Fusion measurement did not reopen both distinct saved archives"
        )
    Stages = ReadMeasMap(Receipt.get("fusion_oracle_stage_sha256"))
    StageHashes = tuple(
        ReadMeasSha(Stages.get(Stage))
        for Stage in ("ControlBefore", "Candidate", "Reopen", "ControlAfter")
    )
    if len(set(StageHashes)) != len(StageHashes):
        raise ValueError("Fusion measurement requires distinct native stage evidence")
    return FreezeMapping(
        {
            KFusionMeasOpt: FreezeMapping(
                {"generated_sha256": Digest, "oracle_build": Candidate["build"]}
            )
        }
    )
