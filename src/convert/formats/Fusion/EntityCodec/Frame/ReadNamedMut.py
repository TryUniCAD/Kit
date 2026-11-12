from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Values.ReadValueMut import ReadValueMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureText


def ReadNamedMut(
    Cursor: MetaCursor, Catalog: EntityCatalog
) -> tuple[NamedMetadata, ...]:
    Entries: list[NamedMetadata] = []
    Names: set[str] = set()
    for _ in range(Cursor.ReadCount(KMaxCount)):
        FieldName = Cursor.ReadText(Maximum=KMaxFeatureText)
        TypeName = Cursor.ReadText(Maximum=KMaxFeatureText)
        if FieldName in Names or TypeName not in Catalog.NamedTypes:
            raise ValueError("Duplicate or unsupported Fusion entity named metadata")
        Names.add(FieldName)
        Entries.append(
            NamedMetadata(
                FieldName,
                TypeName,
                ReadValueMut(Cursor, Catalog.NamedTypes[TypeName], Catalog),
            )
        )
    return tuple(Entries)
