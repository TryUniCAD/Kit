from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot


# later serialized features need the same atom objects as the embedded manager
@DataClass(frozen=True, slots=True)
class AtomMgrGraph:
    FieldsValue: Mapping[str, object]
    MapValue: MapSnapshot
    ReportValue: Mapping[str, object]
