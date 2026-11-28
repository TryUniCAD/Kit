from __future__ import annotations

# component streams need independent round trips because complete base coverage could hide earlier component regressions
KCheck = """
ConfigDocu, ConfigReader = LoadRooted(
    ContainerFile.require("Contents/CMgr"), CodecReg, 1, 19000
)
DefineDocu, DefineReader = LoadDefinition(
    ContainerFile.require("Contents/Definition"), CodecReg, 19000
)
ManagerRead = ConfigDocu.roots[0]
ConfigNodes = [EntryValue["o"] for EntryValue in ManagerRead["f370"]["items"]]
if ConfigDocu.tail or DefineDocu.tail or ConfigReader.left() or DefineReader.left():
    raise RuntimeError("fresh graph has unread bytes")
if StoreRooted(ConfigDocu, CodecReg, 19000) != StreamMap["Contents/CMgr"]:
    raise RuntimeError("configuration graph changed after decoding")
if StoreDefinition(DefineDocu, CodecReg, 19000) != StreamMap["Contents/Definition"]:
    raise RuntimeError("document graph changed after decoding")
if (
    ManagerRead["f360"] is not ConfigNodes[0]
    or ManagerRead["f368"] is not ConfigNodes[0]
):
    raise RuntimeError("current configuration aliases were not preserved")
"""
