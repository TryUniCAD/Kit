from typing import cast as CastValue

from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.MateConstraint import MateConstraint


# unmeasured relationship modes must reject before their names or values can masquerade as ordinary aligned mates
def CheckAsmMate(Value: MateConstraint, RootId: str) -> None:
    RequireAsm(
        Value.owner_definition_id == RootId and str(Value.alignment) == "aligned",
        "mate requires its actual root owner and aligned mode",
    )
    RequireAsm(
        type(CastValue(object, Value.suppressed)) is bool
        and not Value.suppressed
        and type(CastValue(object, Value.driving)) is bool
        and Value.driving,
        "mate requires exact active driving boolean state",
    )
    RequireAsm(
        Value.provenance is None and not Value.attributes,
        "mate has unprojected extensions",
    )
    RequireAsm(
        str(Value.kind) in ("coincident", "parallel", "distance")
        and len(Value.entity_ids) == 2,
        "mate kind or endpoint arity is unqualified",
    )
