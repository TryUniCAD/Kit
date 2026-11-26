from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# symbolic native predicates need their owning graph and inherited fields without copied state
@DataClass(frozen=True, slots=True)
class ExprFrame:
    ContextValue: BodyContext
    ScopeValue: FieldScope
    NodeValue: ArchiveNode
