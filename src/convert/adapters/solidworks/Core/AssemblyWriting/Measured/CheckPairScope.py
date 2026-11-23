from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import (
    CheckAsmShape,
)
from interchange.assembly.AssemblyEnums import MateKind
from interchange.document.Models.DocumentModel import CadDocument


# validate the mate types for selection and retain the assembly shape diagnostic outside the pair
def CheckPairScope(Document: CadDocument) -> None:
    Graph = Document.assembly
    if Graph is None:
        raise ValueError("measured planar publication requires an assembly")
    if (
        len(Graph.instances) == 2
        and len(Graph.mates) == 2
        and {MateValue.kind for MateValue in Graph.mates}
        == {MateKind.KCoincident, MateKind.KDistance}
    ):
        return
    _ = CheckAsmShape(Document)
    raise ValueError(
        "measured planar publication requires two occurrences and its ordered coincident-distance pair"
    )
