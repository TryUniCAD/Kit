from dataclasses import dataclass as DataClass


# contour incidence and unary relation identity must survive a different fresh native line enumeration
@DataClass(frozen=True, slots=True)
class SourceLine:
    EntityId: str
    TargetIndex: int
    IsReversed: bool
    RelationId: str
    AxisKind: str
