from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqConfig import (
    CheckEqConfig,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import (
    CheckPrismRels,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckSingleBoss import (
    CheckSingleBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.MakeThinOwner import (
    MakeThinOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.ReadThinRefs import (
    ReadThinRefs,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinRevOwner import (
    ThinRevOwner,
)


# the saved semantic route needs one complete active history before interpreting the retained native cache
def ReadSavedThin(
    LinkValue: NativeLink, Archive: SldprtArchive, ConfigName: str
) -> ThinRevOwner:
    Manager = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
    for GraphValue in (LinkValue.ConfigValue, LinkValue.ResolvedValue, Manager):
        ReportValue = GraphValue.ReportValue
        if (
            not ReportValue.get("completed")
            or ReportValue.get("missing_schemas")
            or ReportValue.get("provisional_schemas")
        ):
            raise ValueError(
                "SOLIDWORKS saved thin requires fully decoded archive owners"
            )
    CheckEqConfig(Manager.RootValue, ConfigName)
    CheckPrismRels(LinkValue.ConfigValue.RootValue, IsSaved=True)
    Features = IndexFeatures(LinkValue)
    CheckSingleBoss(Features, "moRevolutionThin_c")
    (FeatureValue,) = (
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moRevolutionThin_c"
    )
    ReadThinRefs(LinkValue, FeatureValue, ConfigName)
    NodesValue = tuple(
        EntryValue.EntryValue
        for EntryValue in LinkValue.ResolvedValue.MapValue.EntriesValue
        if isinstance(EntryValue.EntryValue, ArchiveNode)
    )
    return MakeThinOwner(LinkValue, FeatureValue, Features, NodesValue, IsSaved=True)
