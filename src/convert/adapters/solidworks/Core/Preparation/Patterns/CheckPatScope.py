from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.Enums.EnumDocument import Capability
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Records.RecordConfig import Configuration

# this local pattern represents only the ordinary owned part domains
KPatScopeCaps = frozenset(
    {
        Capability.KParameters,
        Capability.KParamHistory,
        Capability.KSupportPlanes,
        Capability.KEditableSketches,
        Capability.KSelections,
        Capability.KBodyStructure,
        Capability.KConfigurations,
    }
)


# projecting a complete portable pattern must refuse any unrepresented document domain
def CheckPatScope(DocumentValue: CadDocument) -> Configuration:
    if type(DocumentValue) is not CadDocument:
        raise ValueError("expected a real neutral CadDocument")
    if (
        DocumentValue.units is not UnitSystem.KMillimeter
        or DocumentValue.schema_version != "1.0"
        or any(
            Value is not None
            for Value in (
                DocumentValue.brep,
                DocumentValue.assembly,
            )
        )
        or DocumentValue.meshes
        or DocumentValue.brep_payloads
        or DocumentValue.diagnostics
        or DocumentValue.materials
        or DocumentValue.source.attributes
        or DocumentValue.capabilities - KPatScopeCaps
    ):
        raise ValueError(
            "oblique pattern needs an ordinary neutral part without additional geometry or semantics"
        )
    if set(DocumentValue.metadata) != {"name"}:
        raise ValueError("only the ordinary neutral part name is admitted as metadata")
    if len(DocumentValue.configurations) != 1:
        raise ValueError("oblique pattern needs one active ordinary configuration")
    ConfigValue = DocumentValue.configurations[0]
    if (
        ConfigValue.active is not True
        or ConfigValue.parent_id is not None
        or ConfigValue.overrides
        or ConfigValue.suppressed_feature_ids
        or ConfigValue.attributes
    ):
        raise ValueError("unsupported configuration state")
    if (
        len(DocumentValue.feature_timeline) != 5
        or len(DocumentValue.parameters) != 6
        or len(DocumentValue.bodies) != 1
        or len(DocumentValue.sketches) != 2
        or len(DocumentValue.support_planes) != 4
        or len(DocumentValue.selections) != 7
    ):
        raise ValueError(
            "oblique pattern needs the complete owned five operation document graph"
        )
    AssertValid(DocumentValue)
    return ConfigValue
