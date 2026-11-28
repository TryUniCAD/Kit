from typing import Literal

from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import (
    CheckAsmShape,
)
from interchange.assembly.AssemblyEnums import MateKind
from interchange.document.Models.DocumentModel import CadDocument


# determine the measured mate scope while retaining existing unqualified shape diagnostics
def CheckPairScope(Document: CadDocument) -> Literal["perpendicular", "coincident-distance"]:
    Graph = Document.assembly
    if Graph is None:
        raise ValueError("measured planar publication requires an assembly")
    if len(Graph.instances) == 2:
        KindsValue = tuple(MateValue.kind for MateValue in Graph.mates)
        if KindsValue == (MateKind.KPerpendicular,):
            return "perpendicular"
        if len(KindsValue) == 2 and set(KindsValue) == {
            MateKind.KCoincident,
            MateKind.KDistance,
        }:
            return "coincident-distance"
    _ = CheckAsmShape(Document)
    raise ValueError(
        "measured planar publication requires two occurrences with a coincident-distance pair or one perpendicular mate"
    )
