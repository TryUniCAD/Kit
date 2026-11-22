from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedMates.ColdMateLayout import KColdMateClasses
from interchange import MateConstraint, Parameter, ParameterRole


# the cold group must link its exact three physical classes to a single live distance driver
def CheckColdGroup(
    NodesValue: tuple[ArchiveNode, ...],
    RuleValues: tuple[MateConstraint, ...],
    ParameterValues: tuple[Parameter, ...],
    FixedFlags: tuple[dict[str, object], ...],
) -> None:
    if (
        tuple(NodeValue.ClassValue.NameValue for NodeValue in NodesValue)
        != KColdMateClasses
    ):
        raise ValueError("cold planar group requires its exact ordered mate classes")
    if tuple(RowValue["fixed"] for RowValue in FixedFlags) != (True, False):
        raise ValueError(
            "cold planar group requires its first actual occurrence to be fixed"
        )
    if len(ParameterValues) != 1:
        raise ValueError("cold planar group requires a single actual driving length")
    Driver = ParameterValues[0]
    Distance = RuleValues[1]
    if (
        Driver.role != ParameterRole.DRIVING
        or Driver.owner_id != Distance.id
        or Driver.value != Distance.value
        or Distance.parameter_ids != (Driver.id,)
        or not Distance.driving
    ):
        raise ValueError("cold planar group distance differs from its live parameter")
