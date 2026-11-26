from collections.abc import Mapping


# literal prefixes and expanded names must retain the same namespace through serialization
def ExpandXmlName(
    NameValue: str, ScopeValue: Mapping[str, str], UseDefault: bool
) -> str:
    if NameValue.startswith("{"):
        return NameValue
    PrefixValue, Divider, LocalName = NameValue.partition(":")
    if Divider:
        NamespaceValue = ScopeValue.get(PrefixValue)
        if not NamespaceValue:
            raise ValueError("authored keyword name has an unbound prefix")
        return f"{{{NamespaceValue}}}{LocalName}"
    NamespaceValue = ScopeValue.get("") if UseDefault else None
    return f"{{{NamespaceValue}}}{NameValue}" if NamespaceValue else NameValue
