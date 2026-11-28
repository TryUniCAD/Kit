from math import isclose as IsClose

from convert.adapters.Fusion.Measurement.CheckFuseCube import CheckDriver, CheckFuseCube
from convert.adapters.Fusion.Measurement.CheckFuseState import (
    IsSameState,
    ReadFuseState,
)
from convert.adapters.Fusion.Measurement.ReadFuseMeas import ReadMeasNum
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec


# driver changes must affect analytic cuboid geometry and survive both native reopenings
def CheckFuseEdit(
    EditValue: dict[str, object], Rebuilt: dict[str, object], SpecValue: DocumentSpec
) -> None:
    Original = ReadMeasNum(EditValue.get("original_value")) * 10.0
    Changed = ReadMeasNum(EditValue.get("edited_value")) * 10.0
    Measured = ReadFuseState(EditValue.get("measured"))
    if (
        EditValue.get("parameter") != SpecValue.ParamName
        or EditValue.get("unit") != "cm"
        or not IsClose(Original, SpecValue.LengthMm, rel_tol=1e-8, abs_tol=1e-7)
        or IsClose(Original, Changed, rel_tol=1e-8, abs_tol=1e-7)
        or not IsSameState(Measured, EditValue.get("reopened"))
        or not IsSameState(Rebuilt, EditValue.get("restored"))
        or not IsSameState(Rebuilt, EditValue.get("restored_reopened"))
    ):
        raise ValueError("Fusion measurement did not verify a driving edit and reopen")
    CheckFuseCube(Measured, SpecValue, Changed)
    CheckDriver(Measured, SpecValue, Changed)
