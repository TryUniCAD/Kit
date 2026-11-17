from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.MakeModelFeat import (
    MakeModelFeat,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# anonymous mate planes need the complete native atom base before their independent geometric state is assigned
def MakeAtomFeat(OwnerValue: ArchiveNode, TargetValue: FeatureTarget) -> ArchiveNode:
    NodeValue = MakeModelFeat("moRefPlane_c", None, OwnerValue, TargetValue)
    NodeValue.FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    NodeValue.FieldsValue.update({NameValue: [] for NameValue in KAtomLists})
    NodeValue.FieldsValue.update(
        {
            "f368": {"n": 0, "items": []},
            "f388": {"n": 0, "items": []},
            "f538": None,
            "f4a0": 1,
        }
    )
    return NodeValue
