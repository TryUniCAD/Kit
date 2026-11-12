from __future__ import annotations
from typing import TYPE_CHECKING, cast as CastValue

if TYPE_CHECKING:
    from interchange.document.models.DocumentModel import CadDocument, AssemblyData
from interchange.brep.topology.BrepModel import BrepModel
from interchange.enums.EnumUnits import UnitSystem
from typing import Mapping as TypeMap


class GeometryAccess:
    locals()["__slots__"] = ()

    @property
    def Metadata(self) -> TypeMap[str, object]:
        return CastValue("CadDocument", self).metadata

    @property
    def Units(self) -> UnitSystem:
        return CastValue("CadDocument", self).units

    @property
    def SchemaVersion(self) -> str:
        return CastValue("CadDocument", self).schema_version

    @property
    def Assembly(self) -> AssemblyData | None:
        return CastValue("CadDocument", self).assembly

    @property
    def BrepModel(self) -> BrepModel | None:
        return CastValue("CadDocument", self).brep
