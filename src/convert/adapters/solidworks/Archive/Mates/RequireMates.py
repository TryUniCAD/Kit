from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Mates.RequireCylMate import RequireCylMate
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the public planar route uses this narrower family set for complete semantic projection
KPlanarClasses = frozenset(
    ("moMateCoincident", "moMateParallel", "moMateDistanceDim_c", "moMatePerpendicular")
)


# null or unrelated roots must never be presented as an empty successful mate list
def RequireMates(RootsValue: tuple[ArchiveNode | None, ...]) -> None:
    if len(RootsValue) == 1 and isinstance(RootsValue[0], ArchiveNode):
        FirstNode = RootsValue[0]
        if FirstNode.ClassValue == RuntimeClass("moMateConcentric", 1):
            RequireCylMate(FirstNode)
            return
    for NodeValue in RootsValue:
        if (
            not isinstance(NodeValue, ArchiveNode)
            or NodeValue.ClassValue.NameValue not in KPlanarClasses
        ):
            raise BodyUnsupported(
                "ordinary mate list requires planar roots or one qualified concentric root"
            )
