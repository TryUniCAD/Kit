from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph


# the ordinary definition accepts only exact authored density types before construction
def MakeOrdPartDef(Settings: ModelDefInput, DensityValue: float) -> ModelDefGraph:
    Density = ReadStyleNum(DensityValue, "SOLIDWORKS part density", 0.0)
    return MakePartDef(Settings, Density)
