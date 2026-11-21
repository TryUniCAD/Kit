from dataclasses import dataclass, field
from math import isclose

from builders.Sketch import ConstructionError, PlaneFrame, _cross, _dot, _unit, _vector


@dataclass(frozen=True, kw_only=True)
class ReferenceFrame(PlaneFrame):
    computed_normal: tuple[float, float, float] = field(init=False)

    def __post_init__(self):
        origin = _vector(value=self.origin, size=3)
        u = _unit(value=self.u)
        v = _unit(value=self.v)
        if not isclose(_dot(left=u, right=v), 0.0, abs_tol=1e-12):
            raise ConstructionError("reference frame axes must be perpendicular")
        normal = _unit(value=_cross(left=u, right=v))
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "u", u)
        object.__setattr__(self, "v", _cross(left=normal, right=u))
        object.__setattr__(self, "computed_normal", normal)

    @property
    def normal(self):
        return self.computed_normal
