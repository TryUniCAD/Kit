from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Core.Writing.Circle.CheckCircMass import CheckCircMass
from convert.adapters.solidworks.Core.Writing.Circle.CheckCircStage import (
    CheckCircStage,
)
from convert.adapters.solidworks.Core.Writing.Circle.ReadCircState import ReadCircState
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# both native setters must target their actual different driving owners and persisted changes
def CheckCircEdit(
    Value: object, OwnerName: str, BeforeValue: float, AfterValue: float
) -> None:
    EditValue = ReadMeasMap(Value)
    Factor = ReadMeasNum(EditValue.get("factor"))
    if (
        EditValue.get("name") != "D1@" + OwnerName
        or type(EditValue.get("setter_status")) is not int
        or EditValue["setter_status"] != 0
        or not IsClose(ReadMeasNum(EditValue.get("before")), BeforeValue, rel_tol=1e-12)
        or not IsClose(ReadMeasNum(EditValue.get("after")), AfterValue, rel_tol=1e-12)
        or not IsClose(AfterValue, BeforeValue * Factor, rel_tol=1e-12)
        or IsClose(BeforeValue, AfterValue, rel_tol=1e-12)
    ):
        raise ValueError("circle report lacks a real persisted edit of its owned D1")


# native acceptance joins the exact model and every successive open edit and reopen state
def CheckCircTrail(
    CaseValue: dict[str, object], Digest: str, PlanValue: CirclePlan
) -> tuple[str, str]:
    Initial, Edited, Reopened = ReadMeasRows(CaseValue.get("stages"), 3)
    FirstSha = CheckCircStage(Initial, "open-save", Digest, PlanValue)
    EditSha = CheckCircStage(Edited, "fresh-reopen", FirstSha, PlanValue)
    _ = CheckCircStage(Reopened, "edited-fresh-reopen", EditSha, PlanValue)
    Baseline = ReadCircState(Initial, "snapshot")
    Before = ReadCircState(Edited, "snapshot")
    After = ReadCircState(Edited, "edited_body_snapshot")
    Restored = ReadCircState(Reopened, "snapshot")
    Length = PlanValue.CircleValue.RadiusValue * (2 if PlanValue.IsDiameter else 1)
    if (
        Baseline != Before
        or After != Restored
        or Baseline.CenterValue != After.CenterValue
        or any(
            not IsClose(ActualValue, Expected, rel_tol=1e-12, abs_tol=1e-15)
            for ActualValue, Expected in zip(
                Baseline.CenterValue, PlanValue.CircleValue.CenterValue, strict=True
            )
        )
        or not IsClose(Baseline.RadialValue, Length, rel_tol=1e-12)
        or not IsClose(Baseline.DepthValue, PlanValue.DepthValue, rel_tol=1e-12)
    ):
        raise ValueError("circle measurement differs from authored or reopened state")
    CheckCircEdit(
        Edited.get("radial_edit"),
        PlanValue.SketchName,
        Before.RadialValue,
        After.RadialValue,
    )
    CheckCircEdit(
        Edited.get("depth_edit"),
        PlanValue.FeatureName,
        Before.DepthValue,
        After.DepthValue,
    )
    CheckCircMass(Baseline, PlanValue)
    CheckCircMass(After, PlanValue)
    return ReadMeasSha(Edited.get("record_sha256")), ReadMeasSha(
        Reopened.get("record_sha256")
    )
