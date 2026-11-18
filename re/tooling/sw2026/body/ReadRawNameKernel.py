from types import MappingProxyType

from convert.Geometry.Parasolid import ParaHeaderData
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.ReadXmtArrayMut import ReadXmtArrayMut
from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import ReadXmtValueMut
from convert.adapters.solidworks.Archive.Partition.SchemaHeader import SchemaHeader
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


def read_node(cursor, kind, raw_fields):
    if kind not in KKernelShapes:
        raise ValueError('unicode research reached an unmapped native record')
    shape = KKernelShapes[kind]
    if kind not in cursor.SeenKinds:
        cursor.ExpectBytes(SchemaHeader(shape))
        cursor.SeenKinds.add(kind)
    count = cursor.ReadCount() if any(field.CountValue == 1 for field in shape.FieldsValue) else 0
    if count > 4096:
        raise ValueError('unicode research array exceeds the existing bounded inventory')
    index = cursor.ReadIndex()
    if not index:
        raise ValueError('unicode research record has a null identity')
    fields = {}
    for field in shape.FieldsValue:
        length = count if field.CountValue == 1 else field.CountValue
        if field.EncodingValue == 'c':
            value = cursor.TakeBytes(length if field.CountValue else 1)
            raw_fields[index, field.NameValue] = value
            fields[field.NameValue] = value.decode('latin-1')
        elif field.CountValue:
            fields[field.NameValue] = ReadXmtArrayMut(cursor, field, length, False)
        else:
            fields[field.NameValue] = ReadXmtValueMut(cursor, field, False)
    return XmtNode(index, kind, MappingProxyType(fields))


def read_active(data):
    header = ParaHeaderData(data)
    if (header is None or header.schema != 'SCH_3701250_37102_13006'
        or header.description != ': TRANSMIT FILE (partition) created by modeller version 3701250'):
        raise ValueError('unicode research active kernel profile differs')
    cursor = XmtCursor(data[header.body_offset:])
    nodes = {}
    raw_fields = {}
    while (kind := cursor.ReadKind()) != 1:
        node = read_node(cursor, kind, raw_fields)
        if node.IndexValue in nodes or kind in (3, 4) or len(nodes) >= 4096:
            raise ValueError('unicode research has ambiguous kernel ownership')
        nodes[node.IndexValue] = node
    cursor.FinishRead()
    return MappingProxyType(nodes), MappingProxyType(raw_fields)
