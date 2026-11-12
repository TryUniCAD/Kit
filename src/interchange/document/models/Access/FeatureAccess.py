from __future__ import annotations
from typing import TYPE_CHECKING, cast as CastValue

if TYPE_CHECKING:
    from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.records.RecordDiagnostic import Diagnostic


class FeatureAccess:
    locals()["__slots__"] = ()

    @property
    def FeatureTimeline(self) -> tuple[FeatureStep, ...]:
        return CastValue("CadDocument", self).feature_timeline

    @property
    def Bodies(self) -> tuple[DesignBody, ...]:
        return CastValue("CadDocument", self).bodies

    @property
    def Meshes(self) -> tuple[SurfaceMesh, ...]:
        return CastValue("CadDocument", self).meshes

    @property
    def BrepPayloads(self) -> tuple[BrepPayload, ...]:
        return CastValue("CadDocument", self).brep_payloads

    @property
    def Diagnostics(self) -> tuple[Diagnostic, ...]:
        return CastValue("CadDocument", self).diagnostics

    @property
    def Capabilities(self) -> frozenset[Capability]:
        return CastValue("CadDocument", self).capabilities
