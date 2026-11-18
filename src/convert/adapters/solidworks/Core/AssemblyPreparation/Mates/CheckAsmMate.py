from typing import cast as CastValue

from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.MateConstraint import MateConstraint


# ordinary perpendiculars retain unknown alignment while previously qualified planar kinds preserve their exact aligned requirement
def CheckAsmMate(Value: MateConstraint, RootId: str) -> None:
    RequireAsm(
        Value.owner_definition_id == RootId
        and str(Value.alignment)
        == ("unknown" if str(Value.kind) == "perpendicular" else "aligned"),
        "mate requires its actual owner and qualified relationship alignment",
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
        str(Value.kind) in ("coincident", "parallel", "distance", "perpendicular")
        and len(Value.entity_ids) == 2,
        "mate kind or endpoint arity is unqualified",
    )
