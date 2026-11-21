from __future__ import annotations

# base graph measurements make ownership identifiers and lifecycle evidence reviewable across the process boundary
KBaseMetrics = """
BuildReport.update(
    {
        "base_system_classes": [NodeValue.cls for NodeValue in BaseResolvedDocu.roots],
        "base_system_ids": [NodeValue["f08"] for NodeValue in BaseResolvedDocu.roots],
        "base_system_flags": [NodeValue["f0c"] for NodeValue in BaseResolvedDocu.roots],
        "base_next_id": BaseGraph.next_persistent_id,
        "base_map_count": BaseStoreMap.count,
        "base_resolved_map_start": BaseResolvedDocu.head["base"],
        "base_root_id": BasePartRead["f08"],
        "base_root_flags": BasePartRead["f0c"],
        "base_flag_trace": BaseFlagTrace,
        "reference_classes": [NodeValue.cls for NodeValue in ReferenceRead.roots],
        "reference_components_distinct": (
            FirstReference["f58"] is not SecondReference["f58"]
        ),
        "reference_owners_shared": all(
            NodeValue["f58"]["owner"] is BasePartRead
            for NodeValue in ReferenceRead.roots
        ),
    }
)
"""
