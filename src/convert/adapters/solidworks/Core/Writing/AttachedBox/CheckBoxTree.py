from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import (
    AttachedBoxPlan,
)


# the actual geometric tree must own the verified source names and feature kinds
def CheckBoxTree(
    TreeValue: tuple[dict[str, object], ...], PlanValue: AttachedBoxPlan
) -> None:
    BoxValue = PlanValue.PartSource
    OriginAxes = PlanValue.OriginAxes
    SketchName = BoxValue.ModelValue.sketches[0].name
    Required = (
        ("Front Plane", "RefPlane"),
        ("Top Plane", "RefPlane"),
        ("Right Plane", "RefPlane"),
        (OriginAxes.OriginLabel, "OriginProfileFeature"),
        (SketchName, "ProfileFeature"),
        (BoxValue.SourceFeatureName, "Extrusion"),
        *((Value.LabelValue, "RefAxis") for Value in OriginAxes.AxisValues),
    )
    if len(TreeValue) < len(Required) or any(
        RowValue.get("error") != 0 or RowValue.get("warning") is not False
        for RowValue in TreeValue
    ):
        raise ValueError(
            "attached box measurement reported incomplete native rebuild state"
        )
    Features = TreeValue[-len(Required) :]
    if any(
        (RowValue.get("name"), RowValue.get("type")) != Expected
        or RowValue.get("parent") is not None
        or RowValue.get("suppressed") is not False
        for RowValue, Expected in zip(Features, Required, strict=True)
    ):
        raise ValueError("attached box measurement has different actual feature owners")
