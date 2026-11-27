from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.PartBodyIdentity import KPartBodyId


# an active partition receives the body identity only when native records prove solid ownership
def TypedBodyId(Model: NativeModel) -> str | None:
    if Model.cut_source is not None:
        return KPartBodyId
    if len(Model.operations) == 1:
        Operation = Model.operations[0]
        if Operation.kind == "join" and Operation.archive_spans:
            return KPartBodyId
    return None
