from __future__ import annotations

import math as MathValue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from convert.adapters.solidworks.Core.NativeDimension import NativeDimension
    from convert.adapters.solidworks.Core.Native import NativeRule
    from interchange.geometry.Models.Sketch import SketchEntity


# radial constraints require a unique circle with the same measurement and native operand
def RadialTarget(
    Dimension: NativeDimension,
    RuleValue: NativeRule,
    MarkerCircles: tuple[SketchEntity, ...],
) -> str | None:
    if (
        Dimension.value_mm is not None
        and Dimension.native_offset is not None
        and Dimension.native_role in {"driving", "display"}
        and len(Dimension.operands) == 1
        and (
            (Dimension.kind == "diameter" and "<MOD-DIAM>" in Dimension.source_text)
            or (
                Dimension.kind == "radius"
                and Dimension.source_text.lstrip().startswith("R")
            )
        )
    ):
        Operand = Dimension.operands[0]
        Factor = 2 if Dimension.kind == "diameter" else 1
        Matches = [
            Entity
            for Entity in MarkerCircles
            if MathValue.isclose(
                Entity.geometry.radius * Factor,
                Dimension.value_mm,
                rel_tol=1e-9,
                abs_tol=1e-9,
            )
        ]
        if (
            len(Matches) == 1
            and Matches[0].attributes.get("object_index") == Operand.entity_index + 1
            and sum(
                Entity.attributes.get("object_index") == Operand.entity_index + 1
                for Entity in MarkerCircles
            )
            == 1
            and RuleValue.references
            == (f"native:{Operand.kind_code:04x}:{Operand.entity_index}",)
        ):
            return Matches[0].id
    return None
