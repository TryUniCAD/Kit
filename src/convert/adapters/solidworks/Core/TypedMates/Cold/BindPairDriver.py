from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedMates.Cold.ReadMateDriver import (
    ReadMateDriver,
)
from interchange import MateConstraint, Parameter


# the linked distance parameter must survive as the actual associated neutral parameter
def BindPairDriver(
    NodesValue: tuple[ArchiveNode, ...], RulesValue: tuple[MateConstraint, ...]
) -> tuple[tuple[MateConstraint, ...], tuple[Parameter, ...]]:
    if (
        tuple(Value.ClassValue.NameValue for Value in NodesValue)
        != ("moMateCoincident", "moMateDistanceDim_c")
        or len(RulesValue) != 2
        or RulesValue[0].value is not None
        or any(Value.parameter_ids for Value in RulesValue)
    ):
        raise ValueError("cold planar pair requires its single owned distance driver")
    First, Second = RulesValue
    Driver = ReadMateDriver(NodesValue[1], Second)
    return (First, ReplaceValue(Second, parameter_ids=(Driver.id,))), (Driver,)
