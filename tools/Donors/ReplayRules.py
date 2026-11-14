from __future__ import annotations

KFieldRule = "REP001"

KReplayRule = "REP002"

KRuleNames = {
    KFieldRule: "recorded field operations",
    KReplayRule: "recorded payload replay calls",
}

KReplayNames = frozenset(
    {"ReplayAssembly", "ReplayConfig", "ReplayFixed", "ReplayResolved"}
)

KKindPattern = r"[a-z]+(?::[A-Za-z0-9]+)?"

KRootMarkers = frozenset({"Methods", "Owners"})

KStandardPath = (
    ".agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md"
)
