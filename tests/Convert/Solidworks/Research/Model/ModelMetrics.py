from __future__ import annotations

# component measurements expose input dependence because a successful exit alone cannot prove fresh construction
KMetrics = """
BuildReport = {
    "configuration_names": [ConfigNode["f18"]["f08"] for ConfigNode in ConfigNodes],
    "configuration_ids": [ConfigNode["f08"] for ConfigNode in ConfigNodes],
    "configuration_versions": [ConfigNode["f9a8"] for ConfigNode in ConfigNodes],
    "configuration_node_flags": [ConfigNode["f0c"] for ConfigNode in ConfigNodes],
    "configuration_object_flags": [
        ConfigNode["f4d0"]["f0c"] for ConfigNode in ConfigNodes
    ],
    "next_configuration_id": ManagerRead["f40c"],
    "plane_ids": [PlaneNode["f08"] for PlaneNode in PlaneDocu.roots],
    "plane_normals": [PlaneNode["f6f8"]["normal"] for PlaneNode in PlaneDocu.roots],
    "next_plane_id": NextPlaneId,
    "next_persistent_id": IdAllocator.next_id,
    "system_classes": [ModelNode.cls for ModelNode in SystemDocu.roots],
    "system_ids": [ModelNode["f08"] for ModelNode in SystemDocu.roots],
    "folder_times": [
        ((ModelNode["f2a4"] & 4294967295) << 32 | ModelNode["f2a0"] & 4294967295)
        // 10000000
        - 11644473600
        for ModelNode in SystemDocu.roots[:-1]
    ],
}
"""
