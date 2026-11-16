from __future__ import annotations

# byte identity after decoding protects shared bookkeeping while ownership assertions protect the generated graph
KBaseCheck = """
BaseConfigAgain, BaseStoreAgain = StoreConfigState(BaseConfigDocu, CodecReg, 19000)
if BaseConfigAgain != BaseConfigBytes:
    raise RuntimeError("base configuration changed after decoding")
if (
    StoreResolved(BaseResolvedDocu, CodecReg, 19000, seed=BaseStoreAgain)
    != StreamMap["Contents/Config-0-ResolvedFeatures"]
):
    raise RuntimeError("base system stream changed after decoding")
if not all(
    NodeValue["owner"] is BaseGraph.part for NodeValue in BaseGraph.system_features
):
    raise RuntimeError("base construction lost native ownership")
"""
