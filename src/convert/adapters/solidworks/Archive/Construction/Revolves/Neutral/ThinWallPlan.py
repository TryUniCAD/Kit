from dataclasses import dataclass as DataClass


# a resolved thin spec always owns two display slots even with one active wall
@DataClass(frozen=True, slots=True)
class ThinWallPlan:
    ModeValue: int
    LengthValues: tuple[float, float]
