from __future__ import annotations
from typing import TYPE_CHECKING, cast as CastValue

if TYPE_CHECKING:
    from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordParameter import Parameter
from interchange.records.RecordSource import CadSource


class RootAccess:
    locals()["__slots__"] = ()

    @property
    def Source(self) -> CadSource:
        return CastValue("CadDocument", self).source

    @property
    def Configurations(self) -> tuple[Configuration, ...]:
        return CastValue("CadDocument", self).configurations

    @property
    def Parameters(self) -> tuple[Parameter, ...]:
        return CastValue("CadDocument", self).parameters

    @property
    def SupportPlanes(self) -> tuple[SupportPlane, ...]:
        return CastValue("CadDocument", self).support_planes

    @property
    def Sketches(self) -> tuple[Sketch, ...]:
        return CastValue("CadDocument", self).sketches

    @property
    def Selections(self) -> tuple[Selection, ...]:
        return CastValue("CadDocument", self).selections
