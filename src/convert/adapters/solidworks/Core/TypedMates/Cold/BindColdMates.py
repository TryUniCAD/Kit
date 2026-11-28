from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedMates.Cold.IsColdMateSet import (
    KColdMateClasses,
)
from convert.adapters.solidworks.Core.TypedMates.Cold.ReadMateDriver import (
    ReadMateDriver,
)
from interchange import MateConstraint, Parameter


# the cold graph must own its exact physical classes and bind the live second mate dimension
def BindColdMates(
    NodesValue: tuple[ArchiveNode, ...],
    RulesValue: tuple[MateConstraint, ...],
    FixedFlags: tuple[dict[str, object], ...],
) -> tuple[tuple[MateConstraint, ...], tuple[Parameter, ...]]:
    if (
        tuple(NodeValue.ClassValue.NameValue for NodeValue in NodesValue)
        != KColdMateClasses
    ):
        raise ValueError("cold planar group requires its exact ordered mate classes")
    if tuple(RowValue["fixed"] for RowValue in FixedFlags) != (True, False):
        raise ValueError(
            "cold planar group requires its first actual occurrence to be fixed"
        )
    FirstValue, Distance, LastValue = RulesValue
    if (
        FirstValue.value is not None
        or LastValue.value is not None
        or any(Value.parameter_ids for Value in RulesValue)
    ):
        raise ValueError("cold planar group requires a single actual driving length")
    Driver = ReadMateDriver(NodesValue[1], Distance)
    return (
        FirstValue,
        ReplaceValue(Distance, parameter_ids=(Driver.id,)),
        LastValue,
    ), (Driver,)
