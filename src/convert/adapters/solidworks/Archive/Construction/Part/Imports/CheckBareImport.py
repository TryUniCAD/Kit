from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadBareConfig import (
    ReadBareConfig,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartLabels import PartLabels
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
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
        or DocumentValue.DrawingValue is not None
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


# each synthetic property owner must receive an explicit typed bag even when it is empty
def CheckBareText(PropertiesValue: PartTextInput | None) -> None:
    if PropertiesValue is not None and (
        type(CastValue(object, PropertiesValue)) is not PartTextInput
        or not all(
            isinstance(CastValue(object, ScopeValue), Mapping)
            for ScopeValue in (
                PropertiesValue.SummaryFields,
                PropertiesValue.DocumentFields,
                PropertiesValue.ConfigurationFields,
            )
        )
    ):
        raise ValueError(
            "bare local import text needs three typed literal property bags"
        )


# the selected root configuration and explicit labels must identify the same fresh part
def CheckBareImport(
    DocumentValue: CadDocument,
    InputValue: PartBuildInput,
    LabelsValue: PartLabels,
    LightValues: tuple[LightInput, ...],
) -> BrepModel:
    ModelValue = ReadBareModel(DocumentValue)
    ConfigValue = ReadBareConfig(DocumentValue)
    if ConfigValue.name != LabelsValue.ConfigName:
        raise ValueError(
            "bare local import configuration differs from its neutral owner"
        )
    if (
        LabelsValue.SketchName
        or LabelsValue.AxisValue != "z"
        or not all(
            type(LabelValue) is str and LabelValue.strip() and LabelValue.isprintable()
            for LabelValue in (
                LabelsValue.NameValue,
                LabelsValue.ConfigName,
                LabelsValue.FeatureName,
            )
        )
    ):
        raise ValueError(
            "bare local import needs printable part configuration and feature names"
        )
    LightNames = tuple(LightValue.NameValue for LightValue in LightValues)
    CheckPartInput(DocumentValue, InputValue, LabelsValue, LightNames)
    if InputValue.DesignIntent or InputValue.SelectedLeader:
        raise ValueError("bare local import has no boss presentation owner")
    CheckBareText(InputValue.PropertiesValue)
    return ModelValue
