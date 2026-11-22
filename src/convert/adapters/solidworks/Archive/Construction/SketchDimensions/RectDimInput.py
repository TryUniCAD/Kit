from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# sketch dimension placement and presentation must be authored independently of solved geometry and stored display caches
@DataClass(frozen=True, slots=True)
class RectDimInput:
    WidthText: tuple[float, float]
    HeightText: tuple[float, float]
    DesignIntent: bool
    SelectedLeader: int
    RouteCenter: bool | tuple[bool, bool]
    TextDepths: tuple[float, float] = (0.0, 0.0)

    # malformed presentation must fail before either persistent identities or the existing sketch graph can change
    def __post_init__(self) -> None:
        for PointValue in (self.WidthText, self.HeightText):
            if type(PointValue) is not tuple or len(PointValue) != 2:
                raise TypeError(
                    "rectangle dimension text requires two planar coordinates"
                )
            for Coordinate in PointValue:
                _ = RequireScalar(Coordinate)
        if type(self.TextDepths) is not tuple or len(self.TextDepths) != 2:
            raise TypeError(
                "rectangle dimension text requires one normal offset per driver"
            )
        for Coordinate in self.TextDepths:
            _ = RequireScalar(Coordinate)
        Routes = CastValue(object, self.RouteCenter)
        if type(Routes) is tuple:
            RoutePair = CastValue(tuple[object, ...], Routes)
            ValidRoutes = len(RoutePair) == 2 and all(
                type(Value) is bool for Value in RoutePair
            )
        else:
            ValidRoutes = type(Routes) is bool
        if type(CastValue(object, self.DesignIntent)) is not bool or not ValidRoutes:
            raise TypeError("rectangle dimension preferences require explicit booleans")
        if type(CastValue(object, self.SelectedLeader)) is not int or not -(
            1 << 31
        ) <= self.SelectedLeader < (1 << 31):
            raise ValueError("rectangle dimension leader requires a signed integer")
