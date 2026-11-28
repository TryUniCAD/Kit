from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Core.TypedMates.ReadMateGroup import ReadMateGroup
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange import MateConstraint, MateGroup


# the solved concentric route must retain its same group provenance and single member
def ReadCylGroup(
    LinkValue: NativeLink, GraphValue: MatesGraph, RuleValue: MateConstraint
) -> MateGroup:
    return ReadMateGroup(
        LinkValue, GraphValue, (RuleValue,), RuleValue.owner_definition_id
    )
