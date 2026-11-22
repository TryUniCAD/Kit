from typing import cast as CastValue

from interchange.brep.Topology.BrepModel import BrepModel
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import HasValidCaps
from interchange.Enums.EnumDocument import Capability
from interchange.Records.RecordSource import CadSource


# the bare recipe cannot consume parametric content or untranslated document features
def ReadBareModel(DocumentValue: CadDocument) -> BrepModel:
    if type(CastValue(object, DocumentValue)) is not CadDocument:
        raise TypeError("bare local import requires a typed neutral document")
    if (
        type(DocumentValue.brep) is not BrepModel
        or DocumentValue.schema_version != "1.0"
        or DocumentValue.units != "mm"
        or type(DocumentValue.source) is not CadSource
        or not HasValidCaps(DocumentValue.capabilities)
        or DocumentValue.capabilities - {Capability.KBrep, Capability.KConfigurations}
    ):
        raise ValueError("bare local import requires a neutral millimetre B-rep")
    if (
        DocumentValue.assembly is not None
        or DocumentValue.bodies
        or DocumentValue.feature_timeline
        or DocumentValue.parameters
        or DocumentValue.support_planes
        or DocumentValue.sketches
        or DocumentValue.selections
        or DocumentValue.meshes
        or DocumentValue.materials
        or DocumentValue.brep_payloads
        or DocumentValue.metadata
        or DocumentValue.diagnostics
        or DocumentValue.source.attributes
    ):
        raise ValueError("bare local import has unowned neutral document fields")
    return DocumentValue.brep
