from io import BytesIO
from typing import cast as CastValue, TypeAlias
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import iterparse as ReadEvents

# the xml prefix is implicitly bound in both the authored and serialized tree
KXmlNamespace = "http://www.w3.org/XML/1998/namespace"

# retaining declarations only at their anchors avoids repeated copies of inherited bindings
KXmlScopes: TypeAlias = dict[Element, dict[str, str]]


# namespace events preserve explicit declarations that ordinary element tree attributes omit
def ReadXmlScopes(PayloadValue: bytes) -> tuple[Element, KXmlScopes]:
    ScopesValue: KXmlScopes = {}
    Pending: dict[str, str] = {}
    RootValue: Element | None = None
    for EventName, EventValue in ReadEvents(
        BytesIO(PayloadValue),
        events=("start-ns", "start"),
        forbid_dtd=True,
        forbid_entities=True,
        forbid_external=True,
    ):
        if EventName == "start-ns":
            PrefixValue, NamespaceValue = CastValue(tuple[str, str], EventValue)
            Pending[PrefixValue] = NamespaceValue
        else:
            if RootValue is None:
                RootValue = EventValue
            if Pending:
                ScopesValue[EventValue] = Pending
                Pending = {}
    if RootValue is None:
        raise ValueError("serialized keyword document has no root")
    return RootValue, ScopesValue
