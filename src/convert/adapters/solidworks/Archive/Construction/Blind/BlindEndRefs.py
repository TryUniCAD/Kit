from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# end specifications must retain actual caller owned display graphs and the from end lifecycle object
@DataClass(frozen=True, slots=True)
class BlindEndRefs:
    ForwardValue: ArchiveNode
    ReverseValue: ArchiveNode
    ForwardDraft: ArchiveNode
    ReverseDraft: ArchiveNode
    FromEndValue: ArchiveNode
