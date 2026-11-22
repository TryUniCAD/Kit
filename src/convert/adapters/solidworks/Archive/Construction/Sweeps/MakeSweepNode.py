from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.SweepProfiles import (
    SweepProfiles,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepObjectRows import (
    MakeSweepRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the cold sweep allocates its independent actual feature identity and names both delivered sketch parents in order
def MakeSweepNode(
    NameValue: str,
    PartValue: ArchiveNode,
    ProfilesValue: SweepProfiles,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    SweepValue = ArchiveNode(RuntimeClass("moSweep_c", 1), {})
    InitFeatureMut(SweepValue, NameValue, PartValue, TargetValue, Allocator)
    FieldsValue = SweepValue.FieldsValue
    FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    FieldsValue.update({NameValue: [] for NameValue in KAtomLists})
    FieldsValue.update(
        {
            "f28": FieldInt(FieldsValue, "f28") | 2 | 0x4000,
            "f60": {
                "list": MakeSweepRows(
                    ProfilesValue.SectionValue, ProfilesValue.PathValue
                ),
                "tail": 0,
            },
            "f35c": 0,
            "f368": MakeSweepRows(),
            "f388": MakeSweepRows(),
            "f538": None,
            "f4a0": 1,
            "f544": 1,
            "f6e0": None,
            "f758": None,
            "f780": MakeSweepRows(),
            "f7a0": 0,
            "fc0c": 0,
            "fc10": 1,
            "fc14": 1,
            "fc18": 1,
            "fc1c": 1,
            "f80c": 1,
            "fc20": 0,
            "fc24": 1,
        }
    )
    return SweepValue
