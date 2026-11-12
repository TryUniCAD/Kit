from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Values.EmitValueMut import EmitValueMut
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitText import EmitText
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitNamedMut(Entries: tuple[NamedMetadata, ...], Catalog: EntityCatalog) -> bytes:
    if len({Entry.FieldName for Entry in Entries}) != len(Entries):
        raise ValueError("Duplicate Fusion entity named metadata")
    Output = FeatureSink()
    Output.AddCount(Entries, KMaxCount)
    for Entry in Entries:
        if Entry.TypeName not in Catalog.NamedTypes:
            raise ValueError("Unsupported Fusion entity named metadata metatype")
        Output.AddBytes(EmitText(Entry.FieldName))
        Output.AddBytes(EmitText(Entry.TypeName))
        Output.AddBytes(
            EmitValueMut(Entry.Value, Catalog.NamedTypes[Entry.TypeName], Catalog)
        )
    return bytes(Output.Buffer)
