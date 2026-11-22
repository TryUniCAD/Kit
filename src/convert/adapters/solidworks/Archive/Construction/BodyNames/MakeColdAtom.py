from convert.adapters.solidworks.Archive.Construction.Nodes.InitConceptMut import (
    InitConceptMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the archive body atom needs actual generated feature ownership and constructor neutral state without an invented kernel body
def MakeColdAtom(NameValue: str, AtomId: int, FeatureValue: ArchiveNode) -> ArchiveNode:
    FeatureId = FieldInt(FeatureValue.FieldsValue, "f08")
    if type(AtomId) is not int or not 0 < AtomId < (1 << 31) or FeatureId <= 0:
        raise ValueError("cold atom and feature ids exceed their independent domains")
    AtomValue = ArchiveNode(RuntimeClass("moAtom_c", 1), {})
    InitConceptMut(AtomValue, NameValue)
    AtomValue.FieldsValue.update(
        {
            "f140": AtomId,
            "f144": 0,
            "f130": FeatureId,
            "f12c": FeatureId,
            "f158": 0,
            "body_kind": 0,
            "f170": 0,
            "f18c": 0,
            "f198": -1,
            "f180": 0,
            "f188": 0,
            "f1b0": 0,
            "f19c": 6,
        }
    )
    return AtomValue
