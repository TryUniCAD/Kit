from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the archive references the same selected and activation records as the partition journal
@DataClass(frozen=True, slots=True)
class CylJournal:
    RootValue: XmtNode
    SelectedValue: XmtNode
    InitialValue: XmtNode
    ActivationValue: XmtNode
    RemovedValues: tuple[XmtNode, ...]
