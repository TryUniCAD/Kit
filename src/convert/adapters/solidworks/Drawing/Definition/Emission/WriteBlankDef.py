from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Definition.DefinitionWire import DefinitionWire
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankSchemas import (
    KBlankSchemas,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankVirtuals import (
    KBlankVirtuals,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankGraph import (
    CheckBlankGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.BlankLayouts import (
    KBlankLayouts,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteDrawBody import (
    EmitDrawBodyMut,
)


# blank drawing admission must precede encoding with the shared map and the blank archive layouts
def WriteBlankDef(GraphValue: BlankGraph) -> DefinitionWire:
    CheckBlankGraph(GraphValue)
    ContextValue = BodyContext(
        GraphValue.VersionValue, KBlankLayouts, KBlankVirtuals, KBlankSchemas
    )
    return EmitDrawBodyMut(GraphValue, ContextValue)
