from __future__ import annotations

# container decoding must preserve separate owned allocations while keeping their actual model relationship shared
KReferenceLoad = """
ReferenceRead, ReferenceReader = LoadResolved(
    ContainerFile.require("Research/PlaneReferences"),
    CodecReg,
    19000,
    archive=ContainerFile,
    name="Contents/Config-0-ResolvedFeatures",
    seed=BaseLoadMap,
)
if ReferenceRead.tail or ReferenceReader.left():
    raise RuntimeError("component references have unread bytes")
if (
    StoreResolved(ReferenceRead, CodecReg, 19000, seed=BaseStoreAgain)
    != StreamMap["Research/PlaneReferences"]
):
    raise RuntimeError("component references changed after decoding")
if len(ReferenceRead.roots) != 2:
    raise RuntimeError("component reference count changed after decoding")
FirstReference, SecondReference = ReferenceRead.roots
if FirstReference is SecondReference:
    raise RuntimeError("independent wrappers became shared")
if FirstReference["f58"] is SecondReference["f58"]:
    raise RuntimeError("independent component copies became shared")
if any(
    ReferenceNode["f58"] is BasePartRead["f990"]
    or ReferenceNode["f58"]["owner"] is not BasePartRead
    for ReferenceNode in ReferenceRead.roots
):
    raise RuntimeError("component copy ownership changed after decoding")
"""
