from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeDefHead import (
    MakeDefHead,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeDefTail import (
    MakeDefTail,
)
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefClsid import KPartDefClass
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# ordinary part generation needs a complete typed graph before any definition bytes are emitted
def MakePartDef(Settings: ModelDefInput, DensityValue: float) -> ModelDefGraph:
    NativeDensity = ReadStyleNum(DensityValue, "SOLIDWORKS part density", 0.0)
    if NativeDensity <= 0:
        raise ValueError("SOLIDWORKS part density must be positive")
    FieldValues = MakeDefHead(Settings) | MakeDefTail() | {"f1688": NativeDensity}
    return ModelDefGraph(ArchiveNode(KPartDefClass, FieldValues), Settings.VersionValue)
