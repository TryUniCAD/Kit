from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.document.Models.DocumentModel import AssemblyData
from interchange.assembly.MateGroup import MateGroup


# complete mate membership must retain the actual group name instead of inventing or silently discarding organization
def ReadAsmGroup(GraphValue: AssemblyData, RootId: str) -> MateGroup:
    RequireAsm(
        len(GraphValue.mate_groups) == 1, "one complete ordered mate group is required"
    )
    (GroupValue,) = GraphValue.mate_groups
    RequireAsm(
        GroupValue.owner_definition_id == RootId
        and not GroupValue.parent_group_id
        and type(GroupValue.order) is int
        and GroupValue.order == 0,
        "mate group has unsupported ownership or hierarchy",
    )
    RequireAsm(
        GroupValue.provenance is None and not GroupValue.attributes,
        "mate group has unprojected extensions",
    )
    return GroupValue
