from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot


# the next model fields must see the identities allocated while reading the suffix
@DataClass(frozen=True, slots=True)
class CfgMatGraph:
    FieldsValue: Mapping[str, object]
    MapValue: MapSnapshot
    ReportValue: Mapping[str, object]
