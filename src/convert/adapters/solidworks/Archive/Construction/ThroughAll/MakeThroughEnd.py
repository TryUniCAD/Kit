from convert.adapters.solidworks.Archive.Construction.Blind.MakeEndSpec import (
    MakeEndSpec,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import (
    ThroughEndInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the native pruned end graph has no artificial zero length or inactive draft displays
def MakeThroughEnd(InputValue: ThroughEndInput) -> ArchiveNode:
    if type(InputValue) is not ThroughEndInput:
        raise TypeError("through all end construction requires its typed input")
    FromValue = ArchiveNode(RuntimeClass("moFromEndSpec_c", 1), {"t": 0})
    return MakeEndSpec(
        InputValue.ModeValue, InputValue.IsReversed, None, None, None, None, FromValue
    )
