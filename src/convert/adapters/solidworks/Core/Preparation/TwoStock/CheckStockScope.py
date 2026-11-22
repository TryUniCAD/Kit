from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability


# the bounded stock writer has no native source state or cached bodies to carry forward
def CheckStockScope(DocumentValue: CadDocument) -> None:
    CheckPlainScope(DocumentValue)
    if (
        DocumentValue.units != "mm"
        or DocumentValue.assembly is not None
        or DocumentValue.brep is not None
        or DocumentValue.brep_payloads
        or DocumentValue.meshes
        or DocumentValue.materials
        or not DocumentValue.capabilities <= KPartWriteCaps | {Capability.KSelections}
    ):
        raise ValueError(
            "two-stock preparation needs ordinary cache-free millimetre part intent"
        )
    if (
        len(DocumentValue.configurations),
        len(DocumentValue.parameters),
        len(DocumentValue.support_planes),
        len(DocumentValue.sketches),
        len(DocumentValue.selections),
        len(DocumentValue.feature_timeline),
        len(DocumentValue.bodies),
    ) != (1, 2, 2, 3, 1, 3, 2):
        raise ValueError(
            "two-stock preparation needs two independent bosses and one selected cut"
        )
    ConfigValue = DocumentValue.configurations[0]
    if (
        ConfigValue.name != "Default"
        or ConfigValue.active is not True
        or ConfigValue.parent_id is not None
        or ConfigValue.overrides
        or ConfigValue.suppressed_feature_ids
        or ConfigValue.attributes
    ):
        raise ValueError(
            "two-stock preparation needs one ordinary active Default configuration"
        )
    DocumentValue.assert_valid()
