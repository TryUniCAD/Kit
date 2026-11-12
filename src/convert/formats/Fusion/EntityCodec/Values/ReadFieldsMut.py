from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.formats.Fusion.MetaCursor import MetaCursor


def ReadFieldsMut(
    Cursor: MetaCursor,
    Fields: tuple[FieldSpec, ...],
    Catalog: EntityCatalog,
    Depth: int,
    Reader: KReadValue,
) -> tuple[NamedValue, ...]:
    return tuple(
        NamedValue(Field.FieldName, Reader(Cursor, Field.ValueType, Catalog, Depth + 1))
        for Field in Fields
        if Field.IsSaved
    )
