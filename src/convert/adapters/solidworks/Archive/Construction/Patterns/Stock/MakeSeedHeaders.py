from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import (
    MakeRootLog,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockGraph import (
    SeedStockGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# both physical headers must advertise creation times for the same allocated feature owners
def MakeSeedHeaders(
    GraphValue: SeedStockGraph, *LaterValues: ArchiveNode
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode]:
    SystemValue = GraphValue.SystemValue
    SettingsValue = GraphValue.SettingsValue
    Allocator = GraphValue.Allocator
    OwnersValue = (
        GraphValue.PlateValue.FeatureValue,
        GraphValue.SeedValue.FeatureValue,
        *LaterValues,
    )
    if len(set(OwnersValue)) != len(OwnersValue) or any(
        OwnerValue.FieldsValue.get("owner") is not SystemValue.RootValue
        or Allocator.Allocations.get((OwnerValue, "f08"))
        != FieldInt(OwnerValue.FieldsValue, "f08")
        for OwnerValue in OwnersValue
    ):
        raise ValueError("raised seed headers require actual allocated feature owners")
    HeadersValue = MakePartHeaders(SystemValue, SettingsValue, Allocator)
    for HeaderValue in HeadersValue[:2]:
        LogValues = RequireNode(
            HeaderValue.FieldsValue.get("f20"), "suObList"
        ).FieldsValue
        RootLogs = LogValues.get("items")
        if not isinstance(RootLogs, tuple):
            raise ValueError("raised seed header requires its fresh root creation row")
        LogRows = CastValue(tuple[object, ...], RootLogs)
        if len(LogRows) != 1:
            raise ValueError("raised seed header requires its fresh root creation row")
        LogValues["items"] = (
            *LogRows,
            *(
                MakeRootLog(OwnerValue, SettingsValue.HeaderValue)
                for OwnerValue in OwnersValue
            ),
        )
    return HeadersValue
