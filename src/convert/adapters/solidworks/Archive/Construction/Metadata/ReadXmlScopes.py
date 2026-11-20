from io import BytesIO
from typing import cast as CastValue, TypeAlias
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import iterparse as ReadEvents

# the xml prefix is implicitly bound in both the authored and serialized tree
KXmlNamespace = "http://www.w3.org/XML/1998/namespace"

# resolved names and names written as attribute values share each parsed element namespace scope
XmlScopes: TypeAlias = dict[Element, dict[str, str]]


# namespace events preserve declarations that ordinary element tree attributes omit
def ReadXmlScopes(PayloadValue: bytes) -> tuple[Element, XmlScopes]:
    ScopesValue: XmlScopes = {}
    Pending: dict[str, str] = {}
    Parents = [{"xml": KXmlNamespace}]
    for EventName, EventValue in ReadEvents(
        BytesIO(PayloadValue),
        events=("start-ns", "start", "end"),
        forbid_dtd=True,
        forbid_entities=True,
        forbid_external=True,
    ):
        if EventName == "start-ns":
            PrefixValue, NamespaceValue = CastValue(tuple[str, str], EventValue)
            Pending[PrefixValue] = NamespaceValue
        elif EventName == "start":
            ScopeValue = Parents[-1] | Pending
            ScopesValue[EventValue] = ScopeValue
            Parents.append(ScopeValue)
            Pending.clear()
        else:
            _ = Parents.pop()
    return next(iter(ScopesValue)), ScopesValue
