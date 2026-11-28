from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.CheckBaseCtx import CheckBaseCtx
from convert.adapters.solidworks.Archive.Bodies.External.CheckExtShape import (
    CheckExtShape,
)
from convert.adapters.solidworks.Archive.Bodies.CheckConfigMut import CheckConfigMut
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Fillets.CheckFilletKeep import (
    CheckFilletKeep,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Fillets.CheckFilletRows import (
    CheckFilletRows,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.CheckPatDatum import (
    CheckPatDatum,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# conditional research proofs must retain their exact owning graph and archive mode boundaries
def ValidateFields(
    ContextValue: BodyContext,
    ScopeValue: FieldScope,
    NodeValue: ArchiveNode,
    ProfileName: str,
) -> None:
    if ProfileName == "OrdinaryEdgeFillet":
        CheckFilletKeep(ScopeValue.FieldsValue)
        CheckFilletRows(ScopeValue.FieldsValue)
        return
    if ProfileName == "OrdinaryLocalBaseBody":
        CheckBaseCtx(ContextValue)
        return
    if ProfileName == "OrdinaryConfigExternal":
        CheckConfigMut(ContextValue, ScopeValue, NodeValue)
        return
    if ProfileName == "OrdinaryPatternDatum":
        CheckPatDatum(ScopeValue)
        return
    if ProfileName != "OrdinaryExternalFeature":
        raise BodyUnsupported(f"unsupported native field profile {ProfileName}")
    FlagsValue = ContextValue.FlagsValue
    Parents = ContextValue.UsageValue.SchemaPath[:-1]
    if (
        NodeValue.ClassValue != RuntimeClass("moExtFeature_c", 1)
        or not Parents
        or Parents[0] != "moConfigurationMgr_c"
        or Parents[-1] != "moExtFeatureList_c"
        or "moConfiguration_c" not in Parents
        or FlagsValue.get("ctx3d0") != 1
        or any(
            FlagsValue.get(NameValue, 0)
            for NameValue in (
                "plain_cstring_names",
                "owner_is_drawing",
                "conditions",
            )
        )
    ):
        raise BodyUnsupported(
            "unsupported native external feature owner or archive context"
        )
    CheckExtShape(ScopeValue.FieldsValue)
