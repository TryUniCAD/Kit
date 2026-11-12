from collections.abc import Mapping

from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType

KVectorName = "Vector"


def NamedShape(
    TypeName: str, ElementName: str, NamedTypes: Mapping[str, WireType]
) -> WireType:
    if TypeName != KVectorName:
        if ElementName or TypeName not in NamedTypes:
            raise ValueError("Unsupported Fusion entity named metadata metatype")
        return NamedTypes[TypeName]
    Element = NamedTypes.get(ElementName)
    if Element is None or ElementName == KVectorName:
        raise ValueError("Unsupported Fusion named vector element metatype")
    return WireType("sequence", (Element,))
