from convert.adapters.solidworks.Archive.Definition.Construction.MakeDefHead import (
    MakeDefHead,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeDefTail import (
    MakeDefTail,
)
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefSettings,
)
from convert.adapters.solidworks.Archive.Definition.Construction.RequireDefNumber import (
    RequireDefNumber,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# ordinary part density is stored directly in kilograms per cubic metre at the end of the ui document
def MakePartDef(Settings: ModelDefSettings, DensityValue: float) -> ModelDefGraph:
    NativeDensity = RequireDefNumber(DensityValue)
    if NativeDensity <= 0:
        raise ValueError("SOLIDWORKS part density must be positive")
    FieldValues = MakeDefHead(Settings) | MakeDefTail() | {"f1688": NativeDensity}
    return ModelDefGraph(
        ArchiveNode(RuntimeClass("uiPartDoc_c", 1), FieldValues), Settings.VersionValue
    )
