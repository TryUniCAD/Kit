from convert.adapters.solidworks.Archive.Definition.DefinitionWire import DefinitionWire
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef


# the ordinary write boundary accepts only the proved part graph before emitting bytes
def WriteOrdDef(GraphValue: ModelDefGraph) -> DefinitionWire:
    return WriteModelDef(GraphValue, OrdinaryOnly=True)
