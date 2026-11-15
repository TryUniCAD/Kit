from __future__ import annotations

from Core import Obj
from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, u8, f64, cstr, emb, base, time32
from Schema import If, Rep
from defs.ResolvedCore import xo, Cnd, Ctx, Legacy, PARENT, isa, has_condition, obarray


def flag(name):
    return lambda s, ar: s[name] != 0


def signed_count(name):
    return lambda s, ar: max(s[name], 0)


def ulong_count(name):
    return lambda s, ar: s[name] if s[name] < 0x80000000 else 0


def kind_of(name, target):
    return lambda s, ar: isinstance(s[name], Obj) and isa(s[name].cls, target)


def kind_check(name, target):
    return If(lambda s, ar: isinstance(s[name], Obj) and not isa(s[name].cls, target), [
        Legacy(f"{name} not kind of {target} throws"),
    ])


HIERARCHY = {
    "moBEntRef_c": None,
    "moFaceRef_c": "moBEntRef_c",
    "moViewerFaceRef_c": "moFaceRef_c",
    "moShrinkWrapFaceRef_c": "moFaceRef_c",
    "moEdgeRef_c": "moBEntRef_c",
    "moTangChainRef_c": "moBEntRef_c",
    "moVertexRef_c": "moBEntRef_c",
    "moLoopRef_c": "moBEntRef_c",
    "moSilhEdgeRef_c": "moBEntRef_c",
    "moSilhVertexRef_c": "moSilhEdgeRef_c",
    "moCompBEntRef_c": "moCompRef_c",
    "moCompFace_c": "moCompBEntRef_c",
    "moCompVertex_c": "moCompBEntRef_c",
    "moCompLoop_c": "moCompBEntRef_c",
    "moCompSilhVertex_c": "moCompBEntRef_c",
    "moCompCompositeEdge_c": "moCompBEntRef_c",
    "moCompEdge_c": "moCompCompositeEdge_c",
    "moCompSilhEdge_c": "moCompCompositeEdge_c",
    "moRefWrapper_c": None,
    "moFeatureRefWrapper_c": "moRefWrapper_c",
    "moCurveRef_w": "moRefWrapper_c",
    "moLineRef_w": "moCurveRef_w",
    "moTempAxisRef_w": "moLineRef_w",
    "moGeneralCurveRef_w": "moCurveRef_w",
    "moCircleRef_w": "moGeneralCurveRef_w",
    "moSurfaceRef_w": "moRefWrapper_c",
    "moGeneralSurfRef_w": "moSurfaceRef_w",
    "moPlaneRef_w": "moSurfaceRef_w",
    "moCylinderRef_w": "moSurfaceRef_w",
    "moSingleBoundedSurfRef_w": "moSurfaceRef_w",
    "moSingleFaceRef_w": "moSingleBoundedSurfRef_w",
    "moPointRef_w": "moRefWrapper_c",
    "moEndPointRef_w": "moPointRef_w",
    "moSketchExtRef_w": "moRefWrapper_c",
    "moCompXFormWrapper_c": "moRefWrapper_c",
    "moPlaneDataRef_w": "moCompXFormWrapper_c",
    "moSphereRef_w": "moSurfaceRef_w",
    "moConeRef_w": "moSurfaceRef_w",
    "moTorusRef_w": "moSingleFaceRef_w",
    "moOrthogonalPlaneRef_w": "moPlaneRef_w",
    "moLineInPlaneRef_w": "moLineRef_w",
    "moPointInPlaneRef_w": "moPointRef_w",
    "moCurvePointRef_w": "moEndPointRef_w",
    "moXPointRef_w": "moEndPointRef_w",
    "moLoopRef_w": "moRefWrapper_c",
    "moTangChainRef_w": "moRefWrapper_c",
    "moSketchContourRef_w": "moRefWrapper_c",
    "moProfileRef_w": "moRefWrapper_c",
    "moCompSketchEntHandle_c": "moCompFeature_c",
    "moEllipseBackedUpData_c": "moSegmentBackedUpData_c",
    "mo3DConeBackedUpData_c": "mo3DSurfaceBackedUpData_c",
    "mo3DCylinderBackedUpData_c": "mo3DSurfaceBackedUpData_c",
    "mo3DSphereBackedUpData_c": "mo3DSurfaceBackedUpData_c",
    "moBackedUpData_c": None,
    "moPointBackedUpData_c": "moBackedUpData_c",
    "moSegmentBackedUpData_c": "moBackedUpData_c",
    "moLineBackedUpData_c": "moSegmentBackedUpData_c",
    "moArcBackedUpData_c": "moSegmentBackedUpData_c",
    "moParabolaBackedUpData_c": "moSegmentBackedUpData_c",
    "mo3DSurfaceBackedUpData_c": "moBackedUpData_c",
    "mo3DPlaneBackedUpData_c": "mo3DSurfaceBackedUpData_c",
    "moEntityIdRep_c": None,
    "moSurfaceIdRep_c": "moEntityIdRep_c",
    "moEdgeIdRep_c": "moEntityIdRep_c",
    "moSingleSurfIdRep_c": "moSurfaceIdRep_c",
    "moDoubleSurfIdRep_c": "moSurfaceIdRep_c",
    "moTripleSurfIdRep_c": "moSurfaceIdRep_c",
    "moQuadSurfIdRep_c": "moSurfaceIdRep_c",
    "moRefSurfIdRep_c": "moSurfaceIdRep_c",
    "moMirPatrnBaseSurfIdRep_c": "moRefSurfIdRep_c",
    "moModifyingSurfIdRep_c": "moRefSurfIdRep_c",
    "moSingleEdgeIdRep_c": "moEdgeIdRep_c",
    "moDoubleEdgeIdRep_c": "moEdgeIdRep_c",
    "moTripleEdgeIdRep_c": "moEdgeIdRep_c",
    "moRefEdgeIdRep_c": "moEdgeIdRep_c",
    "moRef1EdgeIdRep_c": "moRefEdgeIdRep_c",
    "moRef2EdgeIdRep_c": "moRefEdgeIdRep_c",
    "moDerivedEdgeIdRep_c": "moRefEdgeIdRep_c",
    "moByEdgeSurfIdRep_c": "moSurfaceIdRep_c",
    "moMacroFeatEdgeIdRep_c": "moEdgeIdRep_c",
    "moMacroFeatSurfIdRep_c": "moSurfaceIdRep_c",
}

RTTI_PARENT = {
    "moChainComponent_c": [
        "moContextChainComponent_c"
    ],
    "moCompAtomBody_c": [
        "moCompSolidBody_c", "moCompSurfaceBody_c"
    ],
    "moCompBEntRef_c": [
        "moCompCompositeEdge_c", "moCompFace_c", "moCompLoop_c", "moCompSilhVertex_c", "moCompTangChain_c",
        "moCompVertex_c"
    ],
    "moCompBodyFeature_c": [
        "moCompHoleWzd_c"
    ],
    "moCompBody_c": [
        "moCompComp_c"
    ],
    "moCompCompositeCurve_c": [
        "moCompRefCurve_c", "moCompReferenceCurve_c"
    ],
    "moCompCompositeEdge_c": [
        "moCompEdge_c", "moCompSilhEdge_c"
    ],
    "moCompDrawingFeature_c": [
        "moCompBomFeature_c", "moCompWeldTabFeature_c"
    ],
    "moCompEdge_c": [
        "moCompPatternEdge_c"
    ],
    "moCompFaceMeshFacet_c": [
        "moCompFaceMeshFacetFin_c", "moCompFaceMeshFacetVertex_c", "moCompFaceMeshFacets_c"
    ],
    "moCompFace_c": [
        "moCompFaceMeshFacet_c", "moCompSilhFace_c", "moCompTempSlotAxis_c"
    ],
    "moCompFeature_c": [
        "moCompAttributeFeature_c", "moCompBodyFeature_c", "moCompCompositeCurve_c", "moCompCosmeticWeldBead_c",
        "moCompCurveEdge_c", "moCompDetailCircle_c", "moCompDrawingFeature_c", "moCompProfile_c", "moCompRefGeom_c",
        "moCompSectionLine_c", "moCompSketchEntHandle_c"
    ],
    "moCompProfile_c": [
        "moCompSkContour_c", "moCompSketchBlockPosRef_c"
    ],
    "moCompRefGeomEntRef_c": [
        "moCompRefEdge_c"
    ],
    "moCompRefGeom_c": [
        "moCompCoordAxis_c", "moCompCoordPlane_c", "moCompCoordPoint_c", "moCompCoordSys_c", "moCompRefAxis_c",
        "moCompRefCone_c", "moCompRefCylinder_c", "moCompRefLine_c", "moCompRefPlane_c", "moCompRefPoint_c",
        "moCompRefSphere_c", "moCompRefSurface_c", "moCompRefTorus_c", "moCompSketchPntFeat_c"
    ],
    "moCompRef_c": [
        "moCompAddinPoint_c", "moCompAtomBody_c", "moCompBEntRef_c", "moCompBody_c", "moCompBucketData_c",
        "moCompConfiguration_c", "moCompCustomProperty_c", "moCompFeature_c", "moCompGlobalVar_c", "moCompHolder_c",
        "moCompParameter_c", "moCompRefGeomEntRef_c"
    ],
    "moCompReferenceCurve_c": [
        "moCompHelix_c"
    ],
    "moCompSketchEntHandle_c": [
        "moCompCmarkSketchEntHandle_c"
    ],
    "moCompSurfaceBody_c": [
        "moCompPlaneSectionBody_c"
    ],
    "moComponent_c": [
        "moChainComponent_c", "moUnitComponent_c"
    ],
    "moUnitComponent_c": [
        "moContextUnitComponent_c"
    ],
}

IDREP_PARENT = {
    "moSingleSurfIdRep_c": [
        "moBackDraftSurfIdRep_c", "moDraftSurfIdRep_c", "moFaceBlendSurfIdRep_c", "moFilletSurfIdRep_c",
        "moFromSktBottomSurfIdRep_c", "moFromSktEntSurfIdRep_c", "moFromSktTopSurfIdRep_c", "moRipSurfIdRep_c",
        "moSMWeldBeadFilletSurfaceIdRep_c", "moSimpleCavitySurfIdRep_c", "moSimpleCoreSurfIdRep_c",
        "moSimpleSurfIdRep_c", "moThinOffsetSurfIdRep_c", "moUserSurfIdRep_c",
    ],
    "moDoubleSurfIdRep_c": [
        "moBendEndSurfIdRep_c", "moEndCapChamferSurfIdRep_c", "moEndFaceSurfIdRep_c", "moExtensionSurfIdRep_c",
        "moFormFeatureSurfIdRep_c", "moMoldPartingGeomSurfIdRep_c", "moNetSideSurfIdRep_c",
        "moRadiateCornerSurfIdRep_c", "moRadiateSurfIdRep_c", "moRipSurfIdRep2_c", "moSimpleDoubleSurfIdRep_c",
        "moSimplifiedFeatSurfIdRep_c", "moSweepSideSurfIdRep_c", "moThinClosingSurfIdRep_c", "moUnBendSurfIdRep_c",
        "moWzdHoleSurfIdRep_c",
    ],
    "moTripleSurfIdRep_c": [
        "moCornerRelief3IntSurfIdRep_c", "moEndFace3IntSurfIdRep_c", "moFromSktEnt3IntSurfIdRep_c",
        "moMBimportSurfIdRep_c", "moPenetratedFace3IntSurfIdRep_c", "moSMGussetEndCornerFilletSurfIdRep_c",
        "moSMGussetFromSkEdgeFilletSurfIdRep_c", "moSMGussetLateralCornerFilletSurfIdRep_c",
        "moSMGussetLateralEdgeFilletSurfIdRep_c", "moSideFace3IntSurfIdRep_c", "moSlotSurfIdRep_c",
        "moTabSurfIdRep_c", "moThinClosing3IntSurfIdRep_c", "moThinOffset3IntSurfIdRep_c",
    ],
    "moQuadSurfIdRep_c": ["moFilletVertexFaceSurfaceIdRep_c"],
    "moRefSurfIdRep_c": [
        "moDerivedSurfIdRep2_c", "moDerivedSurfIdRep_c", "moDimPatternSurfIdRep_c", "moEndCapEndSurfIdRep_c",
        "moMacroFeatRefSurfIdRep_c", "moPLineInterSurfIdRep_c", "moPunchSurfIdRep_c", "moShellSurfIdRep_c",
        "structConnectionBodySurfIdRep_c", "structConnectionCutSurfIdRep_c",
    ],
    "moMirPatrnBaseSurfIdRep_c": [
        "moCirPatternSurfIdRep2_c", "moCirPatternSurfIdRep_c", "moCopySurfIdRep_c", "moCurvePatternSurfIdRep_c",
        "moIndirectSurfIdRep2_c", "moIndirectSurfIdRep_c", "moLPatternSurfIdRep_c", "moMirPatternSurfIdRep2_c",
        "moMirPatternSurfIdRep_c", "moSketchPatternSurfIdRep_c", "moTablePatternSurfIdRep_c",
    ],
    "moModifyingSurfIdRep_c": [
        "moBendModifiedSurfIdRep_c", "moMoldPartingLineSurfIdRep_c", "moPLineSurfIdRep_c",
        "moSMWeldBeadSurfaceIdRep_c", "moSurfExtCornerSurfIdRep_c", "moWeldModifiedSurfIdRep_c",
    ],
    "moSingleEdgeIdRep_c": [
        "moBottomEdgeIdRep_c", "moEdgeRefIdRep_c", "moEndEdgeIdRep_c", "moSegmEdgeIdRep_c", "moSimpleEdgeIdRep_c",
        "moSimplifiedFeatEdgeIdRep_c", "moStartEdgeIdRep_c", "moTopEdgeIdRep_c", "moUserEdgeIdRep_c",
        "moWireEdgeIdRep_c",
    ],
    "moDoubleEdgeIdRep_c": [
        "moMoldPartingGeomCornerEdgeIdRep_c", "moMoldPartingGeomEdgeIdRep_c", "moMoldPartingGeomEndEdgeIdRep_c",
        "moMoldPartingGeomOrigEdgeIdRep_c", "moMoldPartingGeomStartEdgeIdRep_c", "moRadiateCornerEdgeIdRep_c",
        "moRadiateEdgeIdRep_c", "moRadiateEndEdgeIdRep_c", "moRadiateOrigEdgeIdRep_c", "moRadiateStartEdgeIdRep_c",
        "moSegmLeftTrimEdgeIdRep_c", "moSegmRightTrimEdgeIdRep_c", "moSimpleDoubleEdgeIdRep_c",
        "moTrimWireExtEdgeIdRep_c",
    ],
    "moTripleEdgeIdRep_c": [
        "moBottom3IntEdgeIdRep_c", "moFromBod3IntEdgeIdRep_c", "moMBimportEdgeIdRep_c",
        "moSegmLeftSculptEdgeIdRep_c", "moSegmRightSculptEdgeIdRep_c", "moTop3IntEdgeIdRep_c",
    ],
    "moRefEdgeIdRep_c": [
        "moCopyEdgeIdRep_c", "moMacroFeatRefEdgeIdRep_c", "moPttnBodyEdgeIdRep_c", "moPunchEdgeIdRep_c",
    ],
    "moRef1EdgeIdRep_c": [
        "moLeftTrimEdgeIdRep_c", "moPLineProjIdRep_c", "moRightTrimEdgeIdRep_c", "moSurfExtNeighborIdRep_c",
        "moTrimExtEdgeIdRep_c",
    ],
    "moRef2EdgeIdRep_c": [
        "moLeftSculptEdgeIdRep_c", "moPLineSilhIdRep_c", "moRightSculptEdgeIdRep_c", "moSurfExtTrimmedEdgeIdRep_c",
    ],
    "moDerivedEdgeIdRep_c": ["moDerivedEdgeIdRep2_c"],
}

IDREP_SERIALIZE = {
    "er.FUN_4bba8790": ["moEntityIdRep_c", "moSurfaceIdRep_c", "moEdgeIdRep_c"],
    "er.FUN_4bbaa6a0": [
        "moBackDraftSurfIdRep_c", "moBottomEdgeIdRep_c", "moDraftSurfIdRep_c", "moEdgeRefIdRep_c", "moEndEdgeIdRep_c",
        "moFaceBlendSurfIdRep_c", "moFilletSurfIdRep_c", "moFromSktBottomSurfIdRep_c", "moFromSktEntSurfIdRep_c",
        "moFromSktTopSurfIdRep_c", "moRipSurfIdRep_c", "moSMWeldBeadFilletSurfaceIdRep_c", "moSegmEdgeIdRep_c",
        "moSimpleCavitySurfIdRep_c", "moSimpleCoreSurfIdRep_c", "moSimpleEdgeIdRep_c", "moSimpleSurfIdRep_c",
        "moSimplifiedFeatEdgeIdRep_c", "moStartEdgeIdRep_c", "moThinOffsetSurfIdRep_c", "moTopEdgeIdRep_c",
        "moUserEdgeIdRep_c", "moUserSurfIdRep_c", "moWireEdgeIdRep_c",
    ],
    "er.FUN_4bba41f0.FUN_4bbab5b0": [
        "moFromSktEnt3IntSurfIdRep_c", "moMBimportSurfIdRep_c", "moMacroFeatSurfIdRep_c",
        "moPenetratedFace3IntSurfIdRep_c", "moSMGussetEndCornerFilletSurfIdRep_c",
        "moSMGussetFromSkEdgeFilletSurfIdRep_c", "moSMGussetLateralCornerFilletSurfIdRep_c",
        "moSMGussetLateralEdgeFilletSurfIdRep_c", "moSideFace3IntSurfIdRep_c", "moSlotSurfIdRep_c",
        "moTabSurfIdRep_c", "moTripleSurfIdRep_c",
    ],
    "er.FUN_4bba41f0.FUN_4bbab920": [
        "moCornerRelief3IntSurfIdRep_c", "moEndFace3IntSurfIdRep_c", "moThinClosing3IntSurfIdRep_c",
        "moThinOffset3IntSurfIdRep_c",
    ],
    "er.FUN_4bba41f0.FUN_4bbabc20": [
        "moBendEndSurfIdRep_c", "moDoubleSurfIdRep_c", "moEndCapChamferSurfIdRep_c", "moExtensionSurfIdRep_c",
        "moFormFeatureSurfIdRep_c", "moMoldPartingGeomSurfIdRep_c", "moNetSideSurfIdRep_c",
        "moRadiateCornerSurfIdRep_c", "moRadiateSurfIdRep_c", "moRipSurfIdRep2_c", "moSimpleDoubleSurfIdRep_c",
        "moSimplifiedFeatSurfIdRep_c", "moSweepSideSurfIdRep_c", "moThinClosingSurfIdRep_c", "moWzdHoleSurfIdRep_c",
    ],
    "er.FUN_4bba41f0.FUN_4bbabca0": ["moEndFaceSurfIdRep_c"],
    "er.FUN_4bba4220": ["moByEdgeSurfIdRep_c"],
    "er.FUN_4bba4250": ["moCirPatternSurfIdRep2_c"],
    "er.FUN_4bba4280": ["moCirPatternSurfIdRep_c"],
    "er.FUN_4bba8410": [
        "moCopyEdgeIdRep_c", "moLeftTrimEdgeIdRep_c", "moPLineProjIdRep_c", "moPunchEdgeIdRep_c",
        "moRightTrimEdgeIdRep_c", "moSurfExtNeighborIdRep_c", "moTrimExtEdgeIdRep_c",
    ],
    "er.FUN_4bba8470": [
        "moBendModifiedSurfIdRep_c", "moCopySurfIdRep_c", "moEndCapEndSurfIdRep_c", "moMoldPartingLineSurfIdRep_c",
        "moPLineSurfIdRep_c", "moPunchSurfIdRep_c", "moSMWeldBeadSurfaceIdRep_c", "moSketchPatternSurfIdRep_c",
        "moSurfExtCornerSurfIdRep_c", "moTablePatternSurfIdRep_c", "moWeldModifiedSurfIdRep_c",
    ],
    "er.FUN_4bba84c0": [
        "moCurvePatternSurfIdRep_c", "moDimPatternSurfIdRep_c", "moLPatternSurfIdRep_c", "moPLineInterSurfIdRep_c",
    ],
    "er.FUN_4bba84f0": ["moDerivedEdgeIdRep2_c"],
    "er.FUN_4bba85c0": ["moDerivedEdgeIdRep_c"],
    "er.FUN_4bba8670": ["moDerivedSurfIdRep2_c"],
    "er.FUN_4bba86d0": ["moDerivedSurfIdRep_c"],
    "er.FUN_4bba8700": [
        "moMoldPartingGeomCornerEdgeIdRep_c", "moMoldPartingGeomEdgeIdRep_c", "moMoldPartingGeomEndEdgeIdRep_c",
        "moMoldPartingGeomOrigEdgeIdRep_c", "moMoldPartingGeomStartEdgeIdRep_c", "moRadiateCornerEdgeIdRep_c",
        "moRadiateEdgeIdRep_c", "moRadiateEndEdgeIdRep_c", "moRadiateOrigEdgeIdRep_c", "moRadiateStartEdgeIdRep_c",
        "moSegmLeftTrimEdgeIdRep_c", "moSegmRightTrimEdgeIdRep_c", "moSimpleDoubleEdgeIdRep_c",
        "moTrimWireExtEdgeIdRep_c",
    ],
    "er.FUN_4bba9910": ["moIndirectSurfIdRep2_c", "moMirPatternSurfIdRep2_c"],
    "er.FUN_4bba9b20": ["moMacroFeatEdgeIdRep_c"],
    "er.FUN_4bba9bb0": ["moMacroFeatRefEdgeIdRep_c"],
    "er.FUN_4bba9c50.FUN_4bbabe60": ["moMacroFeatRefSurfIdRep_c"],
    "er.FUN_4bba9f70": [
        "moIndirectSurfIdRep_c", "moMirPatrnBaseSurfIdRep_c", "moMirPatternSurfIdRep_c", "moRefSurfIdRep_c",
        "moShellSurfIdRep_c", "structConnectionBodySurfIdRep_c", "structConnectionCutSurfIdRep_c",
    ],
    "er.FUN_4bba9c90": [
        "moLeftSculptEdgeIdRep_c", "moPLineSilhIdRep_c", "moPttnBodyEdgeIdRep_c", "moRightSculptEdgeIdRep_c",
        "moSurfExtTrimmedEdgeIdRep_c",
    ],
    "er.FUN_4bba9d20.FUN_4bbabd60": ["moFilletVertexFaceSurfaceIdRep_c"],
    "er.FUN_4bba9d20.FUN_4bbabef0": ["moQuadSurfIdRep_c"],
    "er.FUN_4bbaa700.FUN_4bbab5b0": [
        "moBottom3IntEdgeIdRep_c", "moFromBod3IntEdgeIdRep_c", "moMBimportEdgeIdRep_c",
        "moSegmLeftSculptEdgeIdRep_c", "moSegmRightSculptEdgeIdRep_c", "moTop3IntEdgeIdRep_c",
        "moTripleEdgeIdRep_c",
    ],
    "er.FUN_4bbaa730.FUN_4bbabc20": ["moUnBendSurfIdRep_c"],
}


def entity_ids(count, name):
    return Rep(count, name, [
        Ctx("ctx48", [Legacy("FUN_4bbac610 entity id restore with archive helper +0x48")], [base("moEntityId_c")]),
    ])


def i32s(*names):
    return [i32(n) for n in names]


def define_idreps(reg):
    reg.define("moEntityIdRep_c.FUN_4bba8de0", [
        xo("f08"),
        xo("f10", "moFR_c"),
    ])
    reg.define("er.FUN_4bba8790", [
        Vgt(0x21A, [emb("f10", "moEntityIdRep_c.FUN_4bba8de0")], [Legacy("FUN_4bba8790 pre-0x21b")]),
    ])
    reg.define("er.FUN_4bba9f70", [
        base("er.FUN_4bba8790"),
        Ctx("helper_20", [Legacy("FUN_4bba9f70 archive helper +0x20 set")]),
        Vlt(0x180, [Legacy("FUN_4bba9f70 pre-0x180")], [emb("f38", "moEntityId_c")]),
    ])
    reg.define("er.FUN_4bbaba40", [
        Vlt(0x180, [Legacy("FUN_4bbaba40 pre-0x180")], [emb("f38", "moEntityId_c")]),
        Vgt(0xDAA, [i32("f48")]),
    ])
    reg.define("er.FUN_4bbab5b0", i32s("f38", "f3c", "f40"))
    reg.define("er.FUN_4bbab920", i32s("f38", "f3c", "f40"))
    reg.define("er.FUN_4bbabc20", i32s("f38", "f3c"))
    reg.define("er.FUN_4bbabca0", i32s("f38", "f3c"))
    reg.define("er.FUN_4bbabd60", [Vgt(0x4970, i32s("f38", "f3c", "f40", "f44"))])
    reg.define("er.FUN_4bbabe60", i32s("f48", "f4c", "f50"))
    reg.define("er.FUN_4bbabef0", i32s("f38", "f3c", "f40", "f44"))
    reg.define("er.FUN_4bbaa6a0", [base("er.FUN_4bba8790"), i32("f38")])
    for tail in ("FUN_4bbab5b0", "FUN_4bbab920", "FUN_4bbabc20", "FUN_4bbabca0"):
        reg.define(f"er.FUN_4bba41f0.{tail}", [base("er.FUN_4bba8790"), base(f"er.{tail}")])
    reg.define("er.FUN_4bbaa700.FUN_4bbab5b0", [base("er.FUN_4bba8790"), base("er.FUN_4bbab5b0")])
    reg.define("er.FUN_4bbaa730.FUN_4bbabc20", [base("er.FUN_4bba8790"), base("er.FUN_4bbabc20")])
    reg.define("er.FUN_4bba9c50.FUN_4bbabe60", [base("er.FUN_4bba9f70"), base("er.FUN_4bbabe60")])
    for tail in ("FUN_4bbabd60", "FUN_4bbabef0"):
        reg.define(f"er.FUN_4bba9d20.{tail}", [
            Vgt(0x4970, [base("er.FUN_4bba8790"), base(f"er.{tail}")]),
        ])
    reg.define("er.FUN_4bba4220", [
        base("er.FUN_4bba8790"),
        Vlt(0x180, [Legacy("FUN_4bbab640 by-edge surface id pre-0x180")], [Legacy("FUN_4bbab640 throws at 0x180+")]),
    ])
    reg.define("er.FUN_4bba4250", [base("er.FUN_4bba9f70"), i32("f48"), i32("f4c")])
    reg.define("er.FUN_4bba4280", [
        base("er.FUN_4bba9f70"),
        i32("f48"),
        Vgt(0x23EB, [Vlt(0x23EF, [i32("old_23ec")])]),
    ])
    reg.define("er.FUN_4bba8410", [base("er.FUN_4bba8790"), emb("f38", "moEntityId_c"), i32("f48")])
    reg.define("er.FUN_4bba8470", [base("er.FUN_4bba9f70"), i32("f48")])
    reg.define("er.FUN_4bba84c0", [base("er.FUN_4bba9f70"), i32("f48"), i32("f4c")])
    reg.define("er.FUN_4bba84f0", [
        base("er.FUN_4bba8790"),
        emb("f38", "moEntityId_c"),
        Vgt(0xDAC, [i32("f48")]),
        i32("f50"),
    ])
    reg.define("er.FUN_4bba85c0", [
        base("er.FUN_4bba8790"),
        emb("f38", "moEntityId_c"),
        Vgt(0xDAC, [i32("f48")]),
    ])
    reg.define("er.FUN_4bba8670", [base("er.FUN_4bba8790"), base("er.FUN_4bbaba40"), i32("f50")])
    reg.define("er.FUN_4bba86d0", [base("er.FUN_4bba8790"), base("er.FUN_4bbaba40")])
    reg.define("er.FUN_4bba8700", [base("er.FUN_4bba8790"), i32("f38"), i32("f3c")])
    reg.define("er.FUN_4bba9910", [base("er.FUN_4bba9f70"), i32("f48")])
    reg.define("er.FUN_4bba9b20", [base("er.FUN_4bba8790"), *i32s("f38", "f3c", "f40")])
    reg.define("er.FUN_4bba9bb0", [
        base("er.FUN_4bba8790"),
        emb("f38", "moEntityId_c"),
        *i32s("f48", "f4c", "f50"),
    ])
    reg.define("er.FUN_4bba9c90", [
        base("er.FUN_4bba8790"),
        emb("f38", "moEntityId_c"),
        i32("f48"),
        i32("f4c"),
    ])
    for fn, classes in IDREP_SERIALIZE.items():
        for c in classes:
            reg.define(c, [base(fn)])


def define_brep(reg):
    reg.define("moEntityId_c", [
        Vlt(0x180, [u8("present")]),
        If(lambda s, ar: ver(ar) >= 0x180 or s["present"] != 0, [xo("f08"), kind_check("f08", "moEntityIdRep_c")]),
    ])
    reg.define("moEntRefDownstreamIdData_c", [
        i32("n10"),
        Rep(signed_count("n10"), "f10", [i32("k"), i32("v")]),
        i32("n20"),
        Rep(signed_count("n20"), "f20", [i32("v")]),
        i32("f38"),
        Vgt(0x3358, [i32("f40_0"), i32("f40_1")]),
    ])
    reg.define("moBEntRef_c", [
        u32("f60"),
        u32("f64"),
        u32("f08"),
        Vlt(0x20C, [], [i32("fe8")]),
        Vgt(0x496, [u32("f70")]),
        Vgt(0x8CB, [Vlt(0xA05, [f64("old_8cc"), xo("old_edge", "moEdgeRef_c")])]),
        Vgt(0x991, [Vlt(0xA05, [xo("old_vertex", "moVertexRef_c")])]),
        Vgt(0xA04, [f64("f28"), f64("f30"), xo("f40", "moVertexRef_c")]),
        Vgt(0x931, [Vlt(0xBE8, [xo("old_932")])]),
        entity_ids(ulong_count("f08"), "f10"),
        Vgt(0x536, [
            u32("f48"),
            Vlt(0x542, [entity_ids(ulong_count("f48"), "f50")]),
        ]),
        Vgt(0x23BB, [
            i32("nd0"),
            Rep(signed_count("nd0"), "fd0", [time32("t0"), time32("t1")]),
        ]),
        Vgt(0x332C, [
            i32("fec"),
            i32("has_f18"),
            If(flag("has_f18"), [emb("f18", "moEntRefDownstreamIdData_c")]),
        ]),
    ])
    reg.define("moMultiMatchFaceData_c.FUN_4b75af80", [
        i32("f08"),
        Vlt(0x10E3, [i32("f0c")], [u32("f0c")]),
        u32("f10"),
        i32("f14"),
    ])
    reg.define("moFaceRef_c", [
        base("moBEntRef_c"),
        Cnd(0x80, [], [
            Vgt(0x109B, [
                i32("nf0"),
                Rep(signed_count("nf0"), "ff0", [base("moMultiMatchFaceData_c.FUN_4b75af80")]),
            ]),
        ]),
    ])
    reg.define("moViewerFaceRef_c", [base("moFaceRef_c")])
    reg.define("moShrinkWrapFaceRef_c", [base("moFaceRef_c"), *i32s("ff8", "ffc", "f100")])
    reg.define("moEdgeRef_c", [base("moBEntRef_c")])
    reg.define("moTangChainRef_c", [base("moBEntRef_c")])
    reg.define("moLoopRef_c", [base("moBEntRef_c"), Vgt(0x65C, [u32("ff0")])])
    reg.define("moVertexRef_c", [
        base("moBEntRef_c"),
        Vgt(0xAB4, [
            i32("has_ff0"),
            If(flag("has_ff0"), [emb("ff0", "mgPoint_c.operator>>")]),
            Ctx("drawing", [Vgt(0x3357, i32s("ff8", "ffc", "f100", "f104"))]),
        ]),
    ])
    reg.define("moSilhEdgeRef_c", [
        base("moBEntRef_c"),
        Vlt(0x248, [], [
            xo("f188", "moFaceRef_c"),
            xo("f190", "moFaceRef_c"),
            xo("f198", "moFaceRef_c"),
            Vlt(0x671, [i32("f1a0")], [u32("flags_1a0")]),
            Vge(0xDD4, [f64("f1b0"), f64("f1b8")]),
        ]),
    ])
    reg.define("moSilhVertexRef_c", [base("moSilhEdgeRef_c"), u32("flags_1c8")])


def comp_edge_points():
    return [
        emb("f158", "mgPoint_c.restore"),
        emb("f170", "mgPoint_c.restore"),
        u32("f18c"),
        i32("n140"),
        Rep(signed_count("n140"), "f130", [xo("o")]),
    ]


def comp_edge_extra(s, ar):
    return has_condition(ar, 0x21) or has_condition(ar, 0x200001) or has_condition(ar, 0x8000001)


def define_comp(reg):
    reg.define("moCompBEntRef_c", [
        base("moCompRef_c"),
        Vlt(0x180, [Legacy("moCompBEntRef_c pre-0x180")], [
            u8("has_alias"),
            If(flag("has_alias"), [
                cstr("f08"),
                Vgt(0x45F, [xo("fe8")]),
            ], [
                xo("fe8"),
                kind_check("fe8", "moBEntRef_c"),
            ]),
        ]),
        If(lambda s, ar: 0x9D <= ver(ar) < 0xAB or ver(ar) >= 0xB3, [xo("ff0", "moExtObject_c")]),
    ])
    for c in ("moCompFace_c", "moCompVertex_c", "moCompSilhVertex_c"):
        reg.define(c, [base("moCompBEntRef_c")])
    reg.define("moCompLoop_c", [
        base("moCompBEntRef_c"),
        Vlt(0x67D, [], [xo("f128", "moCompEdge_c")]),
    ])
    reg.define("moCompCompositeEdge_c", [
        base("moCompBEntRef_c"),
        Vlt(0xA1A, [], [
            i32("f188"),
            If(lambda s, ar: (s["f188"] & 6) == 6, comp_edge_points(), [
                Vgt(0xFA2, comp_edge_points()),
                Vgt(0xABB, [
                    If(lambda s, ar: (s["f188"] & 8) != 0, [
                        xo("f190"),
                        xo("f198"),
                    ]),
                ]),
            ]),
        ]),
    ])
    reg.define("moCompEdge_c", [
        base("moCompCompositeEdge_c"),
        If(comp_edge_extra, [Vgt(0xA49, [i32("f1ac"), i32("f1b0")])]),
        Ctx("drawing", [Vge(0x3352, i32s("f1b4", "f1b8", "f1bc", "f1c0"))]),
    ])
    reg.define("moCompTangChain_c", [base("moCompBEntRef_c")])
    reg.define("moCompSilhFace_c", [base("moCompBEntRef_c"), i32("f130")])
    reg.define("moCompTempSlotAxis_c", [
        base("moCompBEntRef_c"),
        xo("f130", "moCompSketchEntHandle_c"),
        kind_check("f130", "moCompSketchEntHandle_c"),
    ])
    reg.define("moCompPatternEdge_c", [base("moCompEdge_c"), *i32s("f1d8", "f1d0", "f1d4")])
    reg.define("moCompFaceMeshFacet_c", [
        base("moCompBEntRef_c"),
        f64("f130"),
        f64("f138"),
        emb("f140", "mgVector_c.restore"),
        Rep(lambda s, ar: 3, "f148", [emb("p", "mgPoint_c.operator>>")]),
    ])
    reg.define("moCompFaceMeshFacetFin_c", [
        base("moCompFaceMeshFacet_c"),
        emb("f150", "mgPoint_c.restore"),
        emb("f158", "mgPoint_c.restore"),
        i32("f160"),
    ])
    reg.define("moCompFaceMeshFacetVertex_c", [
        base("moCompFaceMeshFacet_c"),
        i32("f150"),
        emb("f158", "mgPoint_c.restore"),
    ])
    reg.define("moCompFaceMeshFacets_c", [
        base("moCompFaceMeshFacet_c"),
        i32("n150"),
        Rep(signed_count("n150"), "f150", [f64("x"), f64("y")]),
    ])
    reg.define("moCompSilhEdge_c", [
        base("moCompCompositeEdge_c"),
        Vgt(0x1C09, [
            i32("has_f1b0"),
            If(flag("has_f1b0"), [emb("f1b0", "mgXform_c.restore")]),
        ]),
        Ctx("drawing", [Vgt(0x3351, i32s("f1c0", "f1c4", "f1c8", "f1cc"))]),
    ])


def mg_count_vector_point(name):
    return [
        u16(f"n{name}"),
        If(flag(f"n{name}"), [
            emb(f"{name}_dir", "mgVector_c.restore"),
            If(lambda s, ar: s[f"n{name}"] < 0x8000 and s[f"n{name}"] > 1, [emb(f"{name}_pt", "mgPoint_c.restore")]),
        ]),
    ]


def define_wrappers(reg):
    reg.define("moRefWrapper_c", [
        xo("f58"),
        kind_check("f58", "moCompRef_c"),
        If(kind_of("f58", "sgEntHandle"), [xo("sketch", "sgSketch")]),
        Vlt(100, [], [
            u16("f68"),
            Vgt(100, [xo("f60", "moComponent_c"), kind_check("f60", "moComponent_c")]),
        ]),
        Vgt(0xE9, [i32("f6c")]),
        Vgt(0xF1, [i32("f08")]),
        Vgt(0x157, [u16("has_f10"), If(flag("has_f10"), [emb("f10", "mgXform_c.restore")])]),
        Vgt(0x39D, [u16("has_f18"), If(flag("has_f18"), [emb("f18", "mgXform_c.restore")])]),
        Vgt(0x3B2, [i32("f0c")]),
        Vlt(0x531, [Vgt(0x4E4, [i32("f20")])], [i32("f20")]),
        Vgt(0x73B, [i32("f74"), i32("f78")]),
        Vgt(0x2FAF, [i32("f7c")]),
        Vgt(0xB66, [i32("f50")]),
        Vlt(0xE6A, [], [i32("f70")]),
        Ctx("ctx874", [
            i32("has_f80"),
            If(flag("has_f80"), [emb("f80", "moReferencedConfiguration_c")]),
        ]),
        Vgt(0x1FD1, [i32("f34"), i32("f30")]),
        Vlt(0x2B73, [], [i32("f98")]),
        Vge(0x3B02, [i32("f38")]),
    ])
    reg.define("moFeatureRefWrapper_c", [base("moRefWrapper_c"), u32("fb0")])
    reg.define("moCurveRef_w", [base("moRefWrapper_c"), Vgt(0xFA3, [f64("fb0"), f64("fb8")])])
    reg.define("moLineRef_w", [
        base("moCurveRef_w"),
        Vgt(0x78, [emb("fc8", "mgPoint_c.restore"), emb("fe0", "mgVector_c.restore")]),
        Vge(0x86B, [
            u8("ff8"),
            Vge(0xDD1, [Vlt(0xFA4, [f64("old_fb0"), f64("old_fb8")])]),
        ]),
    ])
    reg.define("moTempAxisRef_w", [
        base("moLineRef_w"),
        Vgt(0x371D, [
            emb("f100", "mgPoint_c.operator>>"),
            emb("f118", "mgPoint_c.operator>>"),
            i32("f130"),
        ]),
    ])
    reg.define("moGeneralCurveRef_w", [
        base("moCurveRef_w"),
        Vlt(0xF3, [], [
            u8("has_fc8"),
            If(flag("has_fc8"), [emb("fc8", "mo_loadBodyFromArchive")]),
        ]),
        If(lambda s, ar: 0x95E <= ver(ar) <= 0xB9B, [Legacy("moGeneralCurveRef_w id list 0x95e-0xb9b")], [
            Vge(0x95E, [u32("fd0")]),
        ]),
        Vgt(0xBAB, [i32("fd4")]),
        Vgt(0xC96, [xo("fe0", "moContourChooser_c")]),
        Vgt(0xDDC, [xo("fd8", "moCompSketchEntHandle_c")]),
        Vgt(0xE0A, [xo("fe8", "moContourChooser_c")]),
    ])
    reg.define("moCircleRef_w", [
        base("moGeneralCurveRef_w"),
        emb("f100", "mgPoint_c.restore"),
        emb("f118", "mgVector_c.restore"),
        f64("f130"),
        Vge(0xFA4, [i32("f138")]),
        Vge(0x104B, mg_count_vector_point("fc0")),
    ])
    reg.define("moSurfaceRef_w", [
        base("moRefWrapper_c"),
        Vgt(0xF22, [f64("fb0"), f64("fb8"), f64("fc0"), f64("fc8")]),
    ])
    reg.define("moGeneralSurfRef_w", [base("moSurfaceRef_w")])
    reg.define("moPlaneRef_w", [
        base("moSurfaceRef_w"),
        Vgt(99, [emb("fd0", "mgPoint_c.restore"), emb("fe8", "mgVector_c.restore")]),
        Vgt(0xDD3, [Vlt(0xF23, [f64("old_b0"), f64("old_b1"), f64("old_b2"), f64("old_b3")])]),
        Vgt(0xE19, [emb("f100", "mgXform_c.restore")]),
        Vge(0xF2A, [emb("f188", "mgPoint_c.restore")]),
    ])
    reg.define("moCylinderRef_w", [
        base("moSurfaceRef_w"),
        Vgt(0x78, [
            emb("fd0", "mgPoint_c.restore"),
            emb("fe8", "mgVector_c.restore"),
            f64("f100"),
            Vgt(0x104A, mg_count_vector_point("f108")),
        ]),
    ])
    reg.define("moSingleBoundedSurfRef_w", [
        base("moSurfaceRef_w"),
        i32("has_fd8"),
        If(flag("has_fd8"), [
            emb("fd8", "mo_loadBodyFromArchive"),
            Vgt(0x50B, [emb("attribs", "rf.suObList")]),
        ]),
        Vge(0xCDD, [u32("fd0")]),
    ])
    reg.define("moSingleFaceRef_w", [base("moSingleBoundedSurfRef_w"), Vgt(0x4F5, [i32("fe0")])])
    reg.define("moPointRef_w", [base("moRefWrapper_c"), Vgt(0x78, [emb("fb0", "mgPoint_c.restore")])])
    reg.define("moEndPointRef_w", [
        base("moPointRef_w"),
        Vlt(0x1FB, [i32("old_ff0")], [f64("ff0")]),
        Vgt(0x726, [i32("ff8")]),
    ])
    reg.define("moSketchExtRef_w", [
        base("moRefWrapper_c"),
        Vge(0x94, [u16("fb0")]),
        Vge(0x8FD, [xo("fb8")]),
    ])
    reg.define("moCompXFormWrapper_c", [
        base("moRefWrapper_c"),
        emb("fb0", "mgXform_c.restore"),
        Vgt(0xB36, [emb("f138", "mgXform_c.restore")]),
    ])
    reg.define("moPlaneDataRef_w", [
        base("moCompXFormWrapper_c"),
        emb("f1c0", "mgPoint_c.restore"),
        emb("f1d8", "mgVector_c.restore"),
        emb("f1f0", "mgVector_c.restore"),
    ])
    reg.define("moSphereRef_w", [
        base("moSurfaceRef_w"),
        Vgt(0x7E9, [emb("fd0", "mgPoint_c.restore"), f64("fe8")]),
    ])
    reg.define("moConeRef_w", [
        base("moSurfaceRef_w"),
        emb("fd0", "mgPoint_c.restore"),
        emb("fe8", "mgVector_c.restore"),
        f64("f100"),
        Vge(0x8F0, [f64("f108")]),
    ])
    reg.define("moTorusRef_w", [
        Vgt(0x10B7, [base("moSingleFaceRef_w")], [base("moSurfaceRef_w")]),
        Vgt(0x10A0, [
            emb("fe8", "mgPoint_c.restore"),
            emb("f100", "mgVector_c.restore"),
            f64("f118"),
            f64("f120"),
        ]),
    ])
    reg.define("moOrthogonalPlaneRef_w", [
        base("moPlaneRef_w"),
        emb("f200", "mgPoint_c.restore"),
        emb("f218", "mgVector_c.restore"),
    ])
    reg.define("moLineInPlaneRef_w", [
        base("moLineRef_w"),
        emb("f100", "mgPoint_c.restore"),
        emb("f118", "mgVector_c.restore"),
    ])
    reg.define("moPointInPlaneRef_w", [base("moPointRef_w"), emb("ff0", "mgPoint_c.restore")])
    reg.define("moCurvePointRef_w", [base("moEndPointRef_w")])
    reg.define("moXPointRef_w", [
        base("moEndPointRef_w"),
        xo("f100"),
        i32("f108"),
        i32("f10c"),
    ])
    reg.define("moLoopRef_w", [
        base("moRefWrapper_c"),
        i32("has_fb0"),
        If(flag("has_fb0"), [emb("fb0", "mo_loadBodyFromArchive")]),
    ])
    reg.define("moTangChainRef_w", [
        base("moRefWrapper_c"),
        i32("nb0"),
        Rep(signed_count("nb0"), "fb0", [
            i32("has"),
            If(flag("has"), [emb("body", "mo_loadBodyFromArchive")]),
        ]),
    ])
    reg.define("moSketchContourRef_w", [
        base("moRefWrapper_c"),
        u32("fb0"),
        i32("fb4"),
        xo("fb8"),
        xo("fc0", "moContourChooser_c"),
    ])
    reg.define("moProfileRef_w", [base("moRefWrapper_c"), Vgt(0x854, [u32("fb0")])])
    reg.provisional("moCompSketchEntHandle_c", [
        Vlt(0x2D1, [Legacy("FUN_4bbab420 pre-0x2d1")], [
            base("moCompFeature_c"),
            xo("ff8"),
            kind_check("ff8", "sgEntHandle"),
            Vgt(0xA95, [u32("f100")]),
        ]),
    ])
    reg.provisional("moCompCmarkSketchEntHandle_c", [
        base("moCompSketchEntHandle_c"),
        Vgt(0xC99, [xo("f110", "moDisplayItem_c")]),
    ])
    reg.provisional("moContourChooser_c", [
        obarray("f08"),
        Vgt(0xE0A, [
            i32("f48"),
            If(flag("f48"), [xo("f40")]),
        ]),
        Vlt(0xB7D, [Legacy("moContourChooser_c pre-0xb7d id list")], [
            i32("f38"),
            Vgt(0xB9B, [i32("f3c")]),
            u16("flags"),
            If(lambda s, ar: s["flags"] > 3, [Legacy("moContourChooser_c flags above 3 throw")]),
            If(lambda s, ar: s["flags"] & 1, [xo("f28", "suObArray")]),
            If(lambda s, ar: s["flags"] & 2, [xo("f30", "suObArray")]),
        ]),
        Vgt(0x810, [i32("f58")]),
    ])


def define_backed_up(reg):
    reg.define("moBackedUpData_c", [])
    reg.define("mo3DSurfaceBackedUpData_c", [])
    reg.define("moPointBackedUpData_c", [emb("f08", "mgPoint_c.operator>>")])
    reg.define("moSegmentBackedUpData_c", [
        xo("f08", "moPointBackedUpData_c"),
        xo("f10", "moPointBackedUpData_c"),
        i32("f18"),
        i32("f1c"),
    ])
    reg.define("moLineBackedUpData_c", [base("moSegmentBackedUpData_c")])
    reg.define("moArcBackedUpData_c", [
        base("moSegmentBackedUpData_c"),
        i32("f20"),
        xo("f28", "moPointBackedUpData_c"),
        xo("f30", "moPointBackedUpData_c"),
        xo("f38", "moLineBackedUpData_c"),
        xo("f40", "moLineBackedUpData_c"),
        xo("f48", "moPointBackedUpData_c"),
    ])
    reg.define("moParabolaBackedUpData_c", [
        base("moSegmentBackedUpData_c"),
        xo("f20", "moPointBackedUpData_c"),
        xo("f28", "moPointBackedUpData_c"),
        Vgt(0x142C, [xo("f30", "moPointBackedUpData_c"), xo("f38", "moPointBackedUpData_c")]),
        Vgt(0xC58, [f64("f40"), f64("f48")]),
    ])
    reg.define("moEllipseBackedUpData_c", [
        base("moSegmentBackedUpData_c"),
        i32("f20"),
        *[xo(f, "moPointBackedUpData_c") for f in ("f28", "f30", "f38", "f40", "f48")],
    ])
    reg.define("mo3DConeBackedUpData_c", [
        emb("f08", "mgVector_c.restore"),
        emb("f20", "mgPoint_c.restore"),
        f64("f38"),
        f64("f40"),
        f64("f48"),
    ])
    reg.define("mo3DCylinderBackedUpData_c", [
        emb("f08", "mgVector_c.restore"),
        emb("f20", "mgPoint_c.restore"),
        f64("f38"),
    ])
    reg.define("mo3DSphereBackedUpData_c", [emb("f08", "mgPoint_c.restore"), f64("f20")])
    reg.define("mo3DPlaneBackedUpData_c", [
        emb("f08", "mgPoint_c.restore"),
        emb("f20", "mgVector_c.restore"),
        emb("f38", "mgVector_c.restore"),
    ])


def define(reg):
    for c, p in HIERARCHY.items():
        if p is not None:
            PARENT.setdefault(c, p)
    for p, classes in RTTI_PARENT.items():
        for c in classes:
            PARENT.setdefault(c, p)
    for p, classes in IDREP_PARENT.items():
        for c in classes:
            PARENT.setdefault(c, p)
    reg.provisional("mgPoint_c.restore", [f64("x"), f64("y"), f64("z")])
    reg.provisional("mgVector_c.restore", [f64("x"), f64("y"), f64("z")])
    reg.provisional("mgPoint_c.operator>>", [f64("x"), f64("y"), f64("z")])
    define_idreps(reg)
    define_brep(reg)
    define_comp(reg)
    define_wrappers(reg)
    define_backed_up(reg)
