from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatOrig import (
    MakePatOrig,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockGraph import (
    SeedStockGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the ordinary pattern initializes its own fields and selects the actual freshly joined seed feature
def MakePatFeature(StockValue: SeedStockGraph, NameValue: str) -> ArchiveNode:
    Pattern = ArchiveNode(RuntimeClass("moLPattern_c", 1), {})
    InitFeatureMut(
        Pattern,
        NameValue,
        StockValue.SystemValue.RootValue,
        StockValue.SettingsValue.TargetValue,
    )
    Fields = Pattern.FieldsValue
    Fields.update(dict.fromkeys(KAtomWords, 0))
    Fields.update({NameKey: [] for NameKey in KAtomLists})
    Fields.update(
        f35c=0,
        f368=MakeObList(),
        f388=MakeObList(),
        f538=None,
        f4a0=1,
        f6e0=None,
        f758=None,
        f780=MakeObList(),
        f7a0=0,
    )
    Fields.update(
        dict.fromkeys(
            (
                "f820",
                "f8e0",
                "f950",
                "f1278",
                "f1280",
                "f1290",
                "f12e8",
                "f12f0",
                "f1300",
                "f1308",
            )
        )
    )
    Fields.update(
        dict.fromkeys(
            (
                "fa00",
                "f948",
                "n870",
                "nf30",
                "fa04",
                "fa08",
                "na10",
                "na30",
                "f1128",
                "n930",
                "f112c",
                "f129c",
                "f12a4",
                "f12e0",
                "f12e4",
                "f1310",
                "f1314",
                "f1328",
                "f132c",
                "f12a0",
            ),
            0,
        )
    )
    Fields.update(
        dict.fromkeys(("f9e0", "f9fc", "f1050", "f1130", "f12f8", "f12fc"), 1)
    )
    Fields.update(
        f9f0=0,
        f1054=0,
        f870=[],
        f930=[],
        f840=MakeObList(),
        ff50=MakeObList(),
        f8e8=MakeObList(),
        ffa0={
            "f30": 1,
            "f48": None,
            "f98": 0,
            "f68": None,
            "f18": MakePoint(),
            "f9c": 0,
        },
        fa50=MakePatOrig(),
        fcb8=MakePatOrig(),
    )
    Fields.update(
        {
            NameKey: ArchiveNode(RuntimeClass("suObList", 1), MakeObList())
            for NameKey in ("f9d8", "f8d8", "f990")
        }
    )
    SeedValue = StockValue.SeedValue.FeatureValue
    Fields["f988"] = ArchiveNode(RuntimeClass("suObList", 1), MakeObList(SeedValue))
    return Pattern
