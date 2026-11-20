from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot


# inline cache reads expose their fields and keep the parent map handoff explicit
@DataClass(frozen=True, slots=True)
class CfgCacheGraph:
    FieldsValue: Mapping[str, object]
    MapValue: MapSnapshot
    ReportValue: Mapping[str, object]
