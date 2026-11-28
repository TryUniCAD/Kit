from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import (
    AttachedBoxPlan,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxMeasArray import (
    BoxMeasArray,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.CheckAxisMeas import (
    CheckAxisMeas,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.CheckBoxText import (
    CheckBoxText,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.CheckBoxTree import (
    CheckBoxTree,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows


# observed physical properties must follow the parameter values that the native rebuild reported
def CheckBoxMass(
    Solid: dict[str, object], BodyName: str, Spans: tuple[float, float, float]
) -> None:
    MassValue = ReadMeasMap(Solid.get("mass"))
    Center = BoxMeasArray(MassValue.get("com"), 3)
    if (
        Solid.get("body_count") != 1
        or Solid.get("name") != BodyName
        or Solid.get("topology") != [8, 12, 6]
    ):
        raise ValueError("attached box measurement lacks its actual one solid topology")
    Length, Width, Height = Spans
    Expected = (
        Length * Width * Height,
        2 * (Length * Width + Length * Height + Width * Height),
        Length / 2,
        -Height / 2,
        Width / 2,
    )
    Actual = (MassValue.get("volume"), MassValue.get("area"), *Center)
    if not all(
        IsClose(RequireScalar(Value), Target, rel_tol=5e-7)
        for Value, Target in zip(Actual, Expected, strict=True)
    ):
        raise ValueError(
            "attached box measurement mass or centre differs from its live stock"
        )


# compare each real native driver and reference with the original source semantics
def BoxTrialState(
    Observation: dict[str, object],
    PlanValue: AttachedBoxPlan,
    InitialDisplay: tuple[float, float, float] | None,
) -> tuple[tuple[float, float, float], tuple[dict[str, object], ...]]:
    SourceValue = PlanValue.PartSource
    Parameters = ReadMeasMap(Observation.get("drivers_m"))
    Names = tuple(
        SourceValue.ParameterBindings[Value.id]
        for NameValue in ("Length", "Width", "Height")
        for Value in SourceValue.ModelValue.parameters
        if Value.name == NameValue
    )
    if (
        len(Names) != 3
        or set(Parameters) != set(Names)
        or (
            InitialDisplay is None
            and (Observation.get("open_errors"), Observation.get("open_warnings"))
            != (0, 0)
        )
    ):
        raise ValueError(
            "attached box measurement has different driver owners or open status"
        )
    First, Second, Third = (ReadMeasNum(Parameters[NameValue]) for NameValue in Names)
    Spans = (First, Second, Third)
    if min(Spans) <= 0.0:
        raise ValueError("attached box measurement needs positive actual dimensions")
    TreeValue = ReadMeasRows(Observation.get("tree"))
    CheckBoxTree(TreeValue, PlanValue)
    CheckBoxText(Observation, SourceValue.PropertiesValue)
    CheckBoxMass(
        ReadMeasMap(Observation.get("solid")), SourceValue.SourceBodyName, Spans
    )
    CheckAxisMeas(
        Observation.get("axes"),
        PlanValue.OriginAxes,
        Spans if InitialDisplay is None else InitialDisplay,
    )
    return Spans, TreeValue
