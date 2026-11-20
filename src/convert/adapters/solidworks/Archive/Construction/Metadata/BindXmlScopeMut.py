from collections.abc import Iterator, Mapping
from contextlib import contextmanager as ContextManager


# explicit bindings must be undone before the next sibling without copying inherited entries
@ContextManager
def BindXmlScopeMut(
    ScopeValue: dict[str, str], Declarations: Mapping[str, str]
) -> Iterator[None]:
    Previous = {PrefixName: ScopeValue.get(PrefixName) for PrefixName in Declarations}
    ScopeValue.update(Declarations)
    try:
        yield
    finally:
        for PrefixName, NamespaceValue in Previous.items():
            if NamespaceValue is None:
                del ScopeValue[PrefixName]
            else:
                ScopeValue[PrefixName] = NamespaceValue
