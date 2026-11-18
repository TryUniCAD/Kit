from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# independent header roles need fresh attribution and log graphs without sharing mutable stamp nodes
@DataClass(frozen=True, slots=True)
class RevisionGraph:
    UsersValue: ArchiveNode
    CompaniesValue: ArchiveNode
    LogsValue: ArchiveNode
