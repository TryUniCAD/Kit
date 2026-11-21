from __future__ import annotations

# generated streams must survive the real container boundary because in memory graphs alone miss framing defects
KContainer = """
BinaryFile = BuildContainer(StreamMap)
ContainerFile = ArchiveFile.from_bytes(BinaryFile)
PlaneDocu, PlaneReader = LoadRooted(
    ContainerFile.require("Research/PrincipalPlanes"), CodecReg, 1, 19000
)
if (
    PlaneDocu.tail
    or PlaneReader.left()
    or StoreRooted(PlaneDocu, CodecReg, 19000) != StreamMap["Research/PrincipalPlanes"]
):
    raise RuntimeError("principal plane graph changed after decoding")
SystemDocu, SystemReader = LoadRooted(
    ContainerFile.require("Research/SystemFeatures"), CodecReg, 1, 19000
)
if (
    SystemDocu.tail
    or SystemReader.left()
    or StoreRooted(SystemDocu, CodecReg, 19000) != StreamMap["Research/SystemFeatures"]
):
    raise RuntimeError("system feature graph changed after decoding")
"""
