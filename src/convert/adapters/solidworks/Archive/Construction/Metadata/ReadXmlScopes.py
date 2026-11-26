from typing import cast as CastValue, TypeAlias
from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Core.Native import ReadXmlEvents

# the xml prefix is implicitly bound in both the authored and serialized tree
KXmlNamespace = "http://www.w3.org/XML/1998/namespace"

# retaining declarations only at their anchors avoids repeated copies of inherited bindings
KXmlScopes: TypeAlias = dict[Element, dict[str, str]]


# namespace events preserve explicit declarations that ordinary element tree attributes omit
def ReadXmlScopes(PayloadValue: bytes) -> tuple[Element, KXmlScopes]:
    ScopesValue: KXmlScopes = {}
    Pending: dict[str, str] = {}
    RootValue: Element | None = None
    for EventName, EventValue in ReadXmlEvents(PayloadValue.decode("utf-8")):
        if EventName == "start-ns":
            PrefixValue, NamespaceValue = CastValue(tuple[str, str], EventValue)
            Pending[PrefixValue] = NamespaceValue
        else:
            NodeValue = CastValue(Element, EventValue)
            if RootValue is None:
                RootValue = NodeValue
            if Pending:
                ScopesValue[NodeValue] = Pending
                Pending = {}
    if RootValue is None:
        raise ValueError("serialized keyword document has no root")
    return RootValue, ScopesValue
