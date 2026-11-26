from types import MappingProxyType

# shared part feature layouts select native virtual targets from their concrete owner
KPartVirtuals = MappingProxyType(
    {
        ("moAmbientLight_c", 1000): "moFeature_c.SerializeXmlData",
        ("moAmbientLight_c", 1016): True,
        ("moAmbientLight_c", 1208): "moConcept_c.SerializeLWData",
        ("moAmbientLight_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moAtom_c", 1208): "moConcept_c.SerializeLWData",
        ("moAtom_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moDirectionLight_c", 1000): "moFeature_c.SerializeXmlData",
        ("moDirectionLight_c", 1016): True,
        ("moDirectionLight_c", 1208): "moConcept_c.SerializeLWData",
        ("moDirectionLight_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moEnvFolder_c", 1000): "moFeature_c.SerializeXmlData",
        ("moEnvFolder_c", 1016): True,
        ("moEnvFolder_c", 1208): "moConcept_c.SerializeLWData",
        ("moEnvFolder_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moPrtExplViewManager_c", 1000): "moFeature_c.SerializeXmlData",
        ("moPrtExplViewManager_c", 1016): True,
        ("moPrtExplViewManager_c", 1208): "moConcept_c.SerializeLWData",
        ("moPrtExplViewManager_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moSheetMetalMaster_c", 1000): "moFeature_c.SerializeXmlData",
        ("moSheetMetalMaster_c", 1016): True,
        ("moSheetMetalMaster_c", 1208): "moConcept_c.SerializeLWData",
        ("moSheetMetalMaster_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moSketchBlockMgr_c", 1000): None,
        ("moSketchBlockMgr_c", 1016): True,
        ("moSketchBlockMgr_c", 1208): "moConcept_c.SerializeLWData",
        ("moSketchBlockMgr_c", 1216): "moConcept_c.SerializeResolvedData",
    }
)
