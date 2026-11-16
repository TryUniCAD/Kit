from __future__ import annotations

# configuration and resolved streams must share one archive map because environment references cross their boundary
KBaseStreams = """
BaseConfigBytes, BaseStoreMap = StoreConfigState(
    StreamDoc("config", {"direct": 0}, [BaseGraph.part]), CodecReg, 19000
)
BaseContext = {
    "model_compressed_stream": 1,
    "model_is_part": 1,
    "cmgr_f658": BaseGraph.configuration_manager["f658"],
}
BaseResolved = StreamDoc(
    "resolved",
    {"base": BaseStoreMap.count, "context": BaseContext},
    list(BaseGraph.system_features),
)
StreamMap["Contents/Config-0"] = BaseConfigBytes
StreamMap["Contents/Config-0-ResolvedFeatures"] = StoreResolved(
    BaseResolved, CodecReg, 19000, seed=BaseStoreMap
)
StreamMap["Contents/CMgr"] = StoreRooted(
    StreamDoc("rooted", {"base": 1}, [BaseGraph.configuration_manager]), CodecReg, 19000
)
"""
