from convert.adapters.solidworks.Archive.Partition.History.XmtDelta import XmtDelta
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# processed header counts and physical staging capacity have separate native meanings
def CheckUndoCounts(MarkValue: XmtNode, DeltaValue: XmtDelta | None) -> None:
    NewCount, DeletedCount, CopyCount = (
        MarkValue.Integer(NameValue)
        for NameValue in ("n_new_nodes", "n_del_nodes", "n_copy_mod_nodes")
    )
    if DeltaValue is None:
        if NewCount or DeletedCount or CopyCount:
            raise ValueError("initial rollback mark has nonempty header counts")
        return
    if (
        not len(DeltaValue.RemovedValue) <= NewCount <= 4096
        or not len(DeltaValue.RestoredValue) <= DeletedCount <= 4096
        or not 0 <= CopyCount <= DeltaValue.CopyCapacity
    ):
        raise ValueError("mark header counts disagree with physical rollback rows")
