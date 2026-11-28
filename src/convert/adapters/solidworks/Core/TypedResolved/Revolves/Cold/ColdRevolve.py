from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# the axis history and analytic body belong to one decoded part
@DataClass(frozen=True, slots=True)
class ColdRevolve:
    LinkValue: NativeLink
    OwnerValue: RevolveOwner
    ShapeValue: PartGeometry
