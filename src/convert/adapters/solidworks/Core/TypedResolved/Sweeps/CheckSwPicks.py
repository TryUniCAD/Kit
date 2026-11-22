from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KGhostPartition
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.BindSwGhosts import (
    BindSwGhosts,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwProfile import (
    ReadSwPick,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwRow import ReadSwRow
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)


# both selected curves must agree with the actual ghost users and embedded section
def CheckSwPicks(
    Archive: SldprtArchive, GraphValue: SwReadGraph, *, Saved: bool
) -> None:
    LinkValue, SweepValue = GraphValue.LinkValue, GraphValue.FeatureValue
    SectionValue, PathValue = GraphValue.SectionValue, GraphValue.PathValue
    DataValue = NativeRecord(SweepValue.FieldsValue.get("f820"))
    SectionPick = RequireNative(ReadSwRow(DataValue.get("f2c0")), "moGeneralCurveRef_w")
    ContactValue = RequireNative(ReadSwRow(DataValue.get("f2e0")), "moWireContact_c")
    PathPick = RequireNative(ContactValue.FieldsValue.get("fe8"), "moGeneralCurveRef_w")
    SectionId = ReadSwPick(LinkValue, SectionPick, SectionValue.FeatureValue)
    PathId = ReadSwPick(LinkValue, PathPick, PathValue.FeatureValue)
    if (
        SectionId == PathId
        or SectionPick is PathPick
        or NativeRecord(SectionPick.FieldsValue.get("fc8")).get("CircleValue")
        != SectionValue.CurveValue
        or PathPick.FieldsValue.get("has_fc8") != 0
    ):
        raise ValueError(
            "SOLIDWORKS sweep picks disagree with their distinct live contours"
        )
    BindSwGhosts(
        Archive.require(KGhostPartition),
        LinkValue.ConfigValue.RootValue,
        SweepValue,
        PathId,
        SectionId,
        GraphValue if Saved else None,
    )
