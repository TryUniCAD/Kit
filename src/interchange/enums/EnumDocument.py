# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.enums.EnumBase import WireEnum


# diagnostic levels let callers distinguish recoverable degradation from invalid documents
class Severity(WireEnum):
    KInfo = "info"
    KWarning = "warning"
    KError = "error"


# capabilities make representation guarantees explicit for planning and validation
class Capability(WireEnum):
    KParameters = "parameters"
    KParamHistory = "parametric_history"
    KSupportPlanes = "support_planes"
    KEditableSketches = "editable_sketches"
    KSelections = "selections"
    KBodyStructure = "body_structure"
    KConfigurations = "configurations"
    KExpressions = "expressions"
    KBrep = "brep"
    KTessellation = "tessellation"
    KAssemblies = "assemblies"
    KAssemblyMates = "assembly_mates"
    KComponentDocs = "component_documents"
    KExternalRefs = "external_references"
    KMaterials = "materials"
    KNativePayloads = "native_payloads"
    KProvenance = "provenance"
    KRoundtripMeta = "roundtrip_metadata"
