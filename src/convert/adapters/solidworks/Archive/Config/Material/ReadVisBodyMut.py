from collections.abc import Mapping
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.Material.MatVisualTypes import (
    KMatVisualClass,
)
from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import KNodeNameClass
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader

# the two tagged children occupy distinct lightweight base roles on the part
KMatVisualRoles: Mapping[tuple[str, ...], RuntimeClass] = MappingProxyType(
    {
        ("moConcept_c.SerializeLWData", "moNode_c.SerializeLWData", "f18"): (
            KNodeNameClass
        ),
        ("moConcept_c.SerializeLWData", "f78"): KMatVisualClass,
    }
)


# an unexpected newly declared child must fail before its body runs
def ReadVisBodyMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, NodeValue: ArchiveNode
) -> None:
    ExpectedClass = KMatVisualRoles.get(tuple(ContextValue.UsageValue.FieldPath))
    if ReaderValue.NestingDepth != 2 or NodeValue.ClassValue != ExpectedClass:
        raise BodyUnsupported("unsupported SOLIDWORKS part material visual body owner")
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
