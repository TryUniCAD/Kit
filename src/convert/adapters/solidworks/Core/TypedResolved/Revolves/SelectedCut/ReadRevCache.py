from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.MapStockBrep import MapStockBrep
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockData import ReadStockData
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadWorldBodies import ReadWorldBodies
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevCutCache import RevCutCache
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevCutLineage import RevCutLineage


# the two saved solids are joined by physical faces after their selected angular ownership is established
def ReadRevCache(Archive: SldprtArchive, LinkValue: NativeLink, Lineage: RevCutLineage) -> RevCutCache:
    StreamName = LinkValue.ConfigName + "-Partition"
    Nodes, Model = ReadStockData(Archive, StreamName)
    Bodies = ReadWorldBodies(Nodes, Lineage.AtomsValue, Lineage.UntouchedValue.NodeValue, Lineage.CutValue.NodeValue)
    return RevCutCache(MapStockBrep(Nodes, Model, Bodies), Bodies, StreamName)
