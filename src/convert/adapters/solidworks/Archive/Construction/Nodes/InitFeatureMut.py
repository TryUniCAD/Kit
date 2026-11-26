from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureSeeds import (
    KFeatureRefs,
    KFeatureTexts,
    KFeatureWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitConceptMut import (
    InitConceptMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.MakeEntityVis import (
    MakeEntityVis,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# qualified concrete constructors share generic feature state while retaining their actual preallocated node and owner identities
def InitFeatureMut(
    NodeValue: ArchiveNode,
    NameValue: str | None,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds | None = None,
) -> None:
    if (
        not isinstance(CastValue(object, OwnerValue), ArchiveNode)
        or type(TargetValue) is not FeatureTarget
    ):
        raise ValueError("fresh features require actual ownership and release target")
    InitConceptMut(NodeValue, NameValue, Allocator)
    FieldsValue: dict[str, object] = dict.fromkeys(KFeatureWords, 0)
    FieldsValue.update(dict.fromkeys(KFeatureRefs, None))
    FieldsValue.update(dict.fromkeys(KFeatureTexts, ""))
    FieldsValue.update(
        {
            "owner": OwnerValue,
            "f29c": 101,
            "has_f1e8": 0,
            "f2b0": TargetValue.FileVersion,
            "f1e0": 0.0,
            "f2b4": TargetValue.DateCode,
            "f2c8": MakeEntityVis(),
            "f300": TargetValue.ServicePack,
            "f301": TargetValue.SubservicePack,
            "hidden": 0,
            "f30c": -1,
            "f98": 2,
            "f2ac": TargetValue.ParasolidVersion,
            "f344": 1,
        }
    )
    NodeValue.FieldsValue.update(FieldsValue)
