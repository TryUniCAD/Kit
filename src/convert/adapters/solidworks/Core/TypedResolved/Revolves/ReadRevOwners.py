from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevolve import (
    ReadRevolve,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveClasses import (
    KRevolveClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# qualification remains limited to a complete single ordinary profile and boss within the witnessed system inventory
def ReadRevOwners(LinkValue: NativeLink) -> tuple[RevolveOwner, ...]:
    Features = IndexFeatures(LinkValue)
    if any(
        NodeValue.ClassValue.NameValue not in KRevolveClasses
        for NodeValue in Features.values()
    ):
        raise ValueError(
            "ordinary revolve history contains another unqualified feature class"
        )
    Revolves = tuple(
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moRevolution_c"
    )
    Profiles = tuple(
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moProfileFeature_c"
    )
    if len(Revolves) != 1 or len(Profiles) != 1:
        raise ValueError(
            "ordinary revolve requires one actual boss and consumed profile"
        )
    return (ReadRevolve(LinkValue, Revolves[0], Features),)
