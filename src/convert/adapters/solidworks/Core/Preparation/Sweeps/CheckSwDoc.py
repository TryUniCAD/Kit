from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepLabels import (
    SweepLabels,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.Enums.EnumUnits import UnitSystem


# only an intact ordinary editable two sketch part can reach the cold sweep writer
def CheckSwDoc(DocumentValue: CadDocument, LabelsValue: SweepLabels) -> None:
    CheckPlainScope(DocumentValue)
    AssertValid(DocumentValue)
    if (
        DocumentValue.units != UnitSystem.KMillimeter
        or DocumentValue.assembly is not None
        or DocumentValue.brep is not None
        or DocumentValue.meshes
        or DocumentValue.brep_payloads
        or DocumentValue.materials
        or DocumentValue.selections
        or not GetDocumentCaps(DocumentValue) <= KPartWriteCaps
        or set(DocumentValue.metadata) != {"name"}
    ):
        raise ValueError(
            "sweep requires an ordinary millimetre part with editable geometry only"
        )
    if (
        len(DocumentValue.configurations) != 1
        or len(DocumentValue.feature_timeline) != 1
        or len(DocumentValue.sketches) != 2
        or len(DocumentValue.bodies) != 1
        or len(DocumentValue.parameters) != 3
    ):
        raise ValueError(
            "sweep requires two actual sketches their drivers and one body density"
        )
    ConfigValue = DocumentValue.configurations[0]
    if (
        ConfigValue.name != LabelsValue.ConfigName
        or ConfigValue.active is not True
        or ConfigValue.parent_id is not None
        or ConfigValue.overrides
        or ConfigValue.suppressed_feature_ids
        or ConfigValue.attributes
    ):
        raise ValueError("sweep requires its ordinary active Default configuration")


from convert.adapters.base.WritePolicy import GetDocumentCaps
