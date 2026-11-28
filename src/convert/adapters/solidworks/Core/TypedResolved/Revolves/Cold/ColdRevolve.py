from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinRevOwner import (
    ThinRevOwner,
)


# the axis history and analytic body belong to one decoded part
@DataClass(frozen=True, slots=True)
class ColdRevolve:
    LinkValue: NativeLink
    OwnerValue: RevolveOwner | ThinRevOwner
    ShapeValue: PartGeometry
