from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

# ordinary planar roots are the only mate families qualified by this codec
KPlanarClasses = frozenset(
    ("moMateCoincident", "moMateParallel", "moMateDistanceDim_c", "moMatePerpendicular")
)


# null or unrelated roots must never be presented as an empty successful mate list
def RequireMates(RootsValue: tuple[ArchiveNode | None, ...]) -> None:
    for NodeValue in RootsValue:
        if (
            not isinstance(NodeValue, ArchiveNode)
            or NodeValue.ClassValue.NameValue not in KPlanarClasses
        ):
            raise BodyUnsupported(
                "ordinary mate list requires a concrete planar mate root"
            )
