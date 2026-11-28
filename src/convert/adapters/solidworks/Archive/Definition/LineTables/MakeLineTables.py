from convert.adapters.solidworks.Archive.Definition.LineTables.LineTableInput import (
    LineTableInput,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.MakeFontBind import (
    MakeFontBind,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.MakeLinePattern import (
    MakeLinePattern,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.OrderFontBinds import (
    OrderFontBinds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# table counts class tags and native map order derive from the actual new semantic graph
def MakeLineTables(InputValue: LineTableInput) -> dict[str, object]:
    if type(InputValue) is not LineTableInput:
        raise TypeError("line table construction requires typed semantic input")
    Patterns = [{"o": MakeLinePattern(Value)} for Value in InputValue.PatternValues]
    Bindings = [
        MakeFontBind(Value) for Value in OrderFontBinds(InputValue.BindingValues)
    ]
    return {
        "f878": {"n": len(Patterns), "styles": Patterns},
        "f870": ArchiveNode(
            RuntimeClass("uiLineFontMgr_c", 1),
            {"n": len(Bindings), "f10": Bindings},
        ),
    }
