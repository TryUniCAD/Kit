from dataclasses import dataclass as MakeDataClass
from typing import cast as CastValue

from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureContract import FeatureDef

# thin wall orientation is independent of the angular sweep side mode
KWallModes = ("one_sided", "opposite", "midplane", "two_sided")


# an explicit feature type prevents solid revolve consumers from ignoring wall intent
@MakeDataClass(frozen=True, slots=True)
class ThinRevolve(FeatureDef):
    SweepValue: AngularRevolve
    WallMode: str
    FirstWallId: str
    SecondWallId: str | None = None

    # each actual wall must have a distinct editable owner
    def __post_init__(self) -> None:
        if type(CastValue(object, self.SweepValue)) is not AngularRevolve:
            raise ValueError("thin revolution requires an angular sweep")
        if self.WallMode not in KWallModes or (
            (self.WallMode == "two_sided") != (self.SecondWallId is not None)
        ):
            raise ValueError("thin revolution wall mode and drivers disagree")
        WallIds = self.GetWallIds()
        if not all(
            isinstance(CastValue(object, Identity), str) and Identity.strip()
            for Identity in WallIds
        ):
            raise ValueError("thin revolution wall ids must be nonempty text")
        if len(set(WallIds)) != len(WallIds) or any(
            Identity
            in (self.SweepValue.AlongParameterId, self.SweepValue.AgainstParameterId)
            for Identity in WallIds
        ):
            raise ValueError("thin revolution parameter roles must be distinct")

    # validation and native planning use the same ordered active wall bindings
    def GetWallIds(self) -> tuple[str, ...]:
        if self.SecondWallId is None:
            return (self.FirstWallId,)
        return self.FirstWallId, self.SecondWallId
