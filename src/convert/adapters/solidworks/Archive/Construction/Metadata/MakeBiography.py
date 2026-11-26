from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# fresh biography has no process session records and must not invent captured telemetry from a previously saved model
def MakeBiography() -> ArchiveNode:
    return ArchiveNode(RuntimeClass("moBiography_c", 1), {"n": 0, "records": []})
