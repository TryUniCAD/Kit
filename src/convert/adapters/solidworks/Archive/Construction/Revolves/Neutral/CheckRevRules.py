from math import dist as Distance
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolveShape import (
    RevolveShape,
)
from interchange.geometry.Models.Sketch import Sketch


# actual local owners determine unary and equal length rules without adding any inferred constraints or selecting the construction line
def CheckRevRules(
    SketchValue: Sketch, ShapeValue: RevolveShape
) -> tuple[tuple[tuple[int, int], ...], tuple[int, int] | None]:
    OrderValue = SketchValue.closed_profile_entity_ids[0]
    Vertices = ShapeValue.VerticesValue
    AxesValue: dict[int, int] = {}
    EqualValue: tuple[int, int] | None = None
    for RuleValue in SketchValue.constraints:
        if (
            RuleValue.parameter_id is not None
            or not RuleValue.driving
            or RuleValue.suppressed
            or RuleValue.attributes
            or any(
                RefValue.entity_id not in OrderValue or RefValue.point
                for RefValue in RuleValue.references
            )
        ):
            raise ValueError("revolve relation must bind actual local contour lines")
        Indices = tuple(
            OrderValue.index(RefValue.entity_id) for RefValue in RuleValue.references
        )
        if RuleValue.kind == "equal":
            if EqualValue is not None or len(Indices) != 2:
                raise ValueError("revolve requires one ordered equal length pair")
            First, Second = Indices
            if (First - Second) % 4 not in (1, 3) or not IsClose(
                Distance(Vertices[First], Vertices[(First + 1) % 4]),
                Distance(Vertices[Second], Vertices[(Second + 1) % 4]),
                rel_tol=0.0,
                abs_tol=1e-10,
            ):
                raise ValueError(
                    "revolve equal length requires an adjacent square pair"
                )
            EqualValue = First, Second
            continue
        if len(Indices) != 1:
            raise ValueError("revolve requires one actual owner per unary relation")
        IndexValue = Indices[0]
        Horizontal = Vertices[IndexValue][1] == Vertices[(IndexValue + 1) % 4][1]
        KindValue = "horizontal" if Horizontal else "vertical"
        if RuleValue.kind != KindValue or IndexValue in AxesValue:
            raise ValueError("revolve requires its actual contour axis relations")
        AxesValue[IndexValue] = 4 if Horizontal else 5
    if len(AxesValue) != 4:
        raise ValueError("revolve requires a unary relation on each contour line")
    return tuple(AxesValue.items()), EqualValue
