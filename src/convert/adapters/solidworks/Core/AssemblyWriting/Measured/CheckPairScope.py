from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmOrder import (
    ReadAsmOrder,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.AssemblyEnums import MateKind
from interchange.document.Models.DocumentModel import CadDocument


# the current measured member set establishes only the two occurrence ordered planar pair
def CheckPairScope(Document: CadDocument) -> None:
    Graph = Document.assembly
    if Graph is None:
        raise ValueError("measured planar publication requires an assembly")
    RequireAsm(
        len(Graph.instances) == 2
        and tuple(Value.kind for Value in sorted(Graph.mates, key=ReadAsmOrder))
        == (MateKind.KCoincident, MateKind.KDistance),
        "measured planar publication requires two occurrences and its ordered coincident-distance pair",
    )
