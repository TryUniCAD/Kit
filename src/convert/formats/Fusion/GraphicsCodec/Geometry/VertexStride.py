from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexFormat import VertexFormat


def VertexStride(Value: VertexFormat) -> int:
    Fields = tuple(
        (
            Entry.TypeCode,
            Entry.UsageCode,
            Entry.WordOffset,
            Entry.StreamIndex,
            Entry.UsageIndex,
            Entry.InstanceMode,
        )
        for Entry in Value.Fields
    )
    if Fields == ((2, 0, 0, 0, 0, 0),):
        return 3
    if Fields == ((2, 0, 0, 0, 0, 0), (2, 1, 3, 0, 0, 0), (1, 2, 6, 0, 0, 0)):
        return 8
    raise ValueError("Unsupported graphics vertex field layout")
