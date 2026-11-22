from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Mates.ReadAsmRule import (
    ReadAsmRule,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.AsmRootData import (
    AsmRootData,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmOrder import (
    ReadAsmOrder,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane


# complete group projection must account for every source mate entity and parameter before publishing any native bundle
def ReadAsmRules(
    Document: CadDocument,
    ModelValue: AsmRootData,
    PlanesValue: Mapping[str, SupportPlane],
) -> tuple[GroupMateIn, ...]:
    RulesValue = tuple(sorted(ModelValue.GraphValue.mates, key=ReadAsmOrder))
    RequireAsm(
        (
            len(RulesValue) in (2, 3)
            or (len(RulesValue) == 1 and str(RulesValue[0].kind) == "perpendicular")
        )
        and tuple(Value.order for Value in RulesValue) == tuple(range(len(RulesValue))),
        "assembly requires an ordered qualified planar group or one perpendicular",
    )
    RequireAsm(
        ModelValue.GroupValue.mate_ids == tuple(Value.id for Value in RulesValue),
        "mate group membership differs from actual order",
    )
    Entities = {Value.id: Value for Value in ModelValue.GraphValue.mate_entities}
    Parameters = {Value.id: Value for Value in Document.parameters}
    Occurrences = {
        Value.id: Index for Index, Value in enumerate(ModelValue.Occurrences)
    }
    DatumAxes = {Value.id: AxisValue for AxisValue, Value in PlanesValue.items()}
    ResultValue: list[GroupMateIn] = []
    UsedEntities: set[str] = set()
    UsedParameters: set[str] = set()
    for Value in RulesValue:
        ResultValue.append(
            ReadAsmRule(
                Value,
                ModelValue.RootValue.id,
                Entities,
                Occurrences,
                DatumAxes,
                Parameters,
            )
        )
        UsedEntities.update(Value.entity_ids)
        UsedParameters.update(Value.parameter_ids)
    RequireAsm(
        set(Entities) == UsedEntities and set(Parameters) == UsedParameters,
        "assembly has unconsumed mate entities or parameters",
    )
    return tuple(ResultValue)
