from dataclasses import dataclass as Dataclass

from interchange.geometry.Models.VectorSpace import SpaceVector


# raw selected endpoint order must survive normalization of the effective angular sweep direction
@Dataclass(frozen=True, slots=True)
class RevolveAxis:
    StartValue: SpaceVector
    EndValue: SpaceVector
    DirectionValue: SpaceVector
    RawDirection: SpaceVector
