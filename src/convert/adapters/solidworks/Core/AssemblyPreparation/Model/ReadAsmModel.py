from convert.adapters.solidworks.Core.AssemblyPreparation.Model.AsmRootData import (
    AsmRootData,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.AsmWriteCaps import KAsmWriteCaps
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmRoot import (
    CheckAsmRoot,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmConfig import (
    ReadAsmConfig,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmDefs import (
    ReadAsmDefs,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmGroup import (
    ReadAsmGroup,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmOccs import (
    ReadAsmOccs,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.document.Models.DocumentModel import AssemblyData, CadDocument
from interchange.Enums.EnumDocument import Capability


# native assembly preparation requires one validated portable ownership graph shared by every later projection
def ReadAsmModel(Document: CadDocument) -> AsmRootData:
    CheckAsmRoot(Document, AllowedCaps=KAsmWriteCaps | {Capability.KAssemblyMates})
    GraphValue = Document.assembly
    RequireAsm(
        type(GraphValue) is AssemblyData and not GraphValue.attributes,
        "portable assembly graph is missing or extended",
    )
    if GraphValue is None:
        raise ValueError("portable assembly graph is missing")
    ConfigValue = ReadAsmConfig(Document)
    RootValue, ChildValue, ChildDocument = ReadAsmDefs(
        Document, GraphValue, ConfigValue
    )
    Occurrences, FixedIndex = ReadAsmOccs(
        GraphValue, RootValue, ChildValue, ChildDocument
    )
    return AsmRootData(
        GraphValue,
        RootValue,
        ChildValue,
        ChildDocument,
        ConfigValue,
        Occurrences,
        FixedIndex,
        ReadAsmGroup(GraphValue, RootValue.id),
    )
