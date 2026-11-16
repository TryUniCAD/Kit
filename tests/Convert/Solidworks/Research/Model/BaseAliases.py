from __future__ import annotations

# cross stream aliases must retain object identity because duplicate environment or owner nodes change semantics
KBaseAliases = """
BasePartRead = BaseConfigDocu.roots[0]
BaseEnvRead = next(
    NodeValue
    for NodeValue in BaseResolvedDocu.roots
    if NodeValue.cls == "moEnvFolder_c"
)
if BasePartRead["f1e0"] is not BaseEnvRead:
    raise RuntimeError("the environment alias was lost across native streams")
if BasePartRead["f990"]["owner"] is not BasePartRead:
    raise RuntimeError("the native self-component alias was lost")
"""
