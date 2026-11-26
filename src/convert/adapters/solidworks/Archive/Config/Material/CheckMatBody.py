from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Material.MatTypes import (
    KDensityClass,
    KModelDataClass,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# inherited tags can bypass body callbacks so their stored link values need checking
def CheckMatBody(NodeValue: ArchiveNode) -> None:
    ClassValue = NodeValue.ClassValue
    Fields = NodeValue.FieldsValue
    if ClassValue == KModelDataClass and Fields["f08"] is not None:
        raise BodyUnsupported("unqualified SOLIDWORKS model data scene")
    if ClassValue == KDensityClass and (
        Fields["f18"] is not None or Fields["f48"] is not None
    ):
        raise BodyUnsupported("unqualified SOLIDWORKS part density links")
