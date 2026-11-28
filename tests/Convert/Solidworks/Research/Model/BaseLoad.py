from __future__ import annotations

# the shared reader must recover the constructed graph because writer self consistency is insufficient
KBaseLoad = """
BaseConfigDocu, BaseConfigReader = LoadConfig(
    ContainerFile.require("Contents/Config-0"), CodecReg, 19000, archive=ContainerFile
)
BaseLoadMap = BaseConfigReader.map_state()
BaseResolvedDocu, BaseResolvedReader = LoadResolved(
    ContainerFile.require("Contents/Config-0-ResolvedFeatures"),
    CodecReg,
    19000,
    archive=ContainerFile,
    name="Contents/Config-0-ResolvedFeatures",
    seed=BaseLoadMap,
)
if BaseConfigDocu.tail or BaseConfigReader.left():
    raise RuntimeError("base configuration has unread bytes")
if BaseResolvedDocu.tail or BaseResolvedReader.left():
    raise RuntimeError("base system graph has unread bytes")
"""
