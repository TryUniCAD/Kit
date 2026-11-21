from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from interchange.Features.FeatureBody import DesignBody


# the same pattern graph supplies the reconstructed solid and its neutral feature owners
@DataClass(frozen=True, slots=True)
class ColdPatPart:
    LinkValue: NativeLink
    OwnerValue: PatternOwner
    GeometryValue: PartGeometry
    BodiesValue: tuple[DesignBody, ...]
