from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AnnotationFrameFields import (
    KAnnotationFrameFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AtomFields import (
    KAtomFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.BaseAnnotationFields import (
    KBaseAnnotationFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConceptFields import (
    KConceptFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ExternalFields import (
    KExternalFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Members.FeatColorFields import (
    KFeatColorFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FinishFields import (
    KFinishFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FontFields import (
    KFontFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FormatAnnotationFields import (
    KFormatAnnotationFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.GeometryFields import (
    KGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.GhostFields import (
    KGhostFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.LabelAnnotationFields import (
    KLabelAnnotationFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Lighting.LightFields import (
    KLightFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Caches.MassCacheFields import (
    KMassCacheFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.MaterialFields import (
    KMaterialFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.OwnerFields import (
    KOwnerFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.AnnotDimRules import (
    KAnnotDimRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.AnnotHelpRules import (
    KAnnotHelpRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.AnnotTableRules import (
    KAnnotTableRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.AnnotViewRules import (
    KAnnotViewRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.DetailRules import (
    KDetailRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.ModelLwRules import (
    KModelLwRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.ModelResRules import (
    KModelResRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartFeatureRules import (
    KPartFeatureRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartOptionRules import (
    KPartOptionRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartPbrRules import (
    KPartPbrRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartRecordRules import (
    KPartRecordRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartRootRules import (
    KPartRootRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartVisualRules import (
    KPartVisualRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.PartMatFields import (
    KPartMatFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.RecordFields import (
    KRecordFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.RelMgrFields import (
    KRelMgrFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Members.ThreadFields import (
    KThreadFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ToleranceHelperFields import (
    KTolHelperFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.UnitFields import (
    KUnitFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Members.ViewFields import (
    KViewFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.GeometryFields import (
    KGeometryFields as KSharedGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.MassPropFields import (
    KMassPropFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ObListFields import (
    KObListFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ReferenceFields import (
    KReferenceFields,
)

# ordinary part configuration registers only owners exercised by its linked native graphs
KPartLayouts = MappingProxyType(
    {
        "RelCacheDimValueMap_c.Serialize": KRelMgrFields[
            "RelCacheDimValueMap_c.Serialize"
        ],
        "gcCurvatureObject_c": KPartRecordRules["gcCurvatureObject_c"],
        "gcXhatch_c": KPartMatFields["gcXhatch_c"],
        "mgBBox_c.restore": KExternalFields["mgBBox_c.restore"],
        "mgMatrix_c.restore": KGeometryFields["mgMatrix_c.restore"],
        "mgVector_c.restore": KSharedGeometryFields["mgVector_c.restore"],
        "mgXform_c.restore": KGeometryFields["mgXform_c.restore"],
        "moAmbientLight_c": KLightFields["moAmbientLight_c"],
        "moAngOrdinateDimDef_c": KAnnotDimRules["moAngOrdinateDimDef_c"],
        "moAngleDimDef_c": KAnnotDimRules["moAngleDimDef_c"],
        "moAngleUserUnits_c": KUnitFields["moAngleUserUnits_c"],
        "moAnnotationDataHelper_c": KFinishFields["moAnnotationDataHelper_c"],
        "moAnnotationDefs_c": KBaseAnnotationFields["moAnnotationDefs_c"],
        "moAnnotationView_c": KAnnotViewRules["moAnnotationView_c"],
        "moArcLengthDimDef_c": KAnnotDimRules["moArcLengthDimDef_c"],
        "moAtomManager_c.FUN_4bcef8d0": KAtomFields["moAtomManager_c.FUN_4bcef8d0"],
        "moAtom_c": KAtomFields["moAtom_c"],
        "moAuxLabelData_c": KLabelAnnotationFields["moAuxLabelData_c"],
        "moBOMTableDefs_c": KAnnotTableRules["moBOMTableDefs_c"],
        "moBalloonDefs_c": KBaseAnnotationFields["moBalloonDefs_c"],
        "moBaseAnnotationDefs_c": KBaseAnnotationFields["moBaseAnnotationDefs_c"],
        "moBaseDimDef_c": KAnnotDimRules["moBaseDimDef_c"],
        "moBendNoteDefs_c": KBaseAnnotationFields["moBendNoteDefs_c"],
        "moBendTableDefs_c": KAnnotTableRules["moBendTableDefs_c"],
        "moBodyVizProps_c.FUN_4c240300": KPartRecordRules[
            "moBodyVizProps_c.FUN_4c240300"
        ],
        "moCThreadRefMgr_c": KThreadFields["moCThreadRefMgr_c"],
        "moCenterMarkSymDataHelper_c": KAnnotHelpRules["moCenterMarkSymDataHelper_c"],
        "moChamferDimDef_c": KAnnotDimRules["moChamferDimDef_c"],
        "moComponent_c": KReferenceFields["moComponent_c"],
        "moConcept_c.SerializeLWData": KFeatureFields["moConcept_c.SerializeLWData"],
        "moConcept_c.SerializeResolvedData": KConceptFields[
            "moConcept_c.SerializeResolvedData"
        ],
        "moDatumDefs_c": KBaseAnnotationFields["moDatumDefs_c"],
        "moDatumFeatureDataHelper_c": KAnnotHelpRules["moDatumFeatureDataHelper_c"],
        "moDatumTargetDataHelper_c": KAnnotHelpRules["moDatumTargetDataHelper_c"],
        "moDensityParameter_c": KPartMatFields["moDensityParameter_c"],
        "moDensityUnits_c": KUnitFields["moDensityUnits_c"],
        "moDetailDefs_c": KDetailRules["moDetailDefs_c"],
        "moDetailLabelData_c": KLabelAnnotationFields["moDetailLabelData_c"],
        "moDiameterDimDef_c": KAnnotDimRules["moDiameterDimDef_c"],
        "moDimDefs_c": KAnnotDimRules["moDimDefs_c"],
        "moDirectionLight_c": KLightFields["moDirectionLight_c"],
        "moDrViewLabelData_c": KLabelAnnotationFields["moDrViewLabelData_c"],
        "moEnergyUnits_c": KUnitFields["moEnergyUnits_c"],
        "moEntVisProp_c": KFeatureFields["moEntVisProp_c"],
        "moEnvFolder_c": KLightFields["moEnvFolder_c"],
        "moFaceVizProps_c.restore": KPartRecordRules["moFaceVizProps_c.restore"],
        "moFamilyTableDefs_c": KAnnotTableRules["moFamilyTableDefs_c"],
        "moFeatColorTab_c": KFeatColorFields,
        "moFeature_c": KFeatureFields["moFeature_c"],
        "moFeature_c.FUN_4bb2b240": KLightFields["moFeature_c.FUN_4bb2b240"],
        "moFeature_c.SerializeXmlData": KFeatureFields["moFeature_c.SerializeXmlData"],
        "moFloatNumberUserUnits_c": KUnitFields["moFloatNumberUserUnits_c"],
        "moFolder_c": KLightFields["moFolder_c"],
        "moForceUnits_c": KUnitFields["moForceUnits_c"],
        "moForwardedFeatRefsList_c.FUN_4bb5ced0": KPartRecordRules[
            "moForwardedFeatRefsList_c.FUN_4bb5ced0"
        ],
        "moFrequencyUserUnits_c": KUnitFields["moFrequencyUserUnits_c"],
        "moGTolDataHelper_c": KTolHelperFields["moGTolDataHelper_c"],
        "moGTolDlgDataFrame_c": KAnnotationFrameFields["moGTolDlgDataFrame_c"],
        "moGeneralTableDefs_c": KAnnotTableRules["moGeneralTableDefs_c"],
        "moGhostBodyIdManager_c.FUN_4bf050e0": KGhostFields[
            "moGhostBodyIdManager_c.FUN_4bf050e0"
        ],
        "moGravityUnits_c": KUnitFields["moGravityUnits_c"],
        "moGtolDefs_c": KBaseAnnotationFields["moGtolDefs_c"],
        "moHoleCalloutDimDef_c": KAnnotDimRules["moHoleCalloutDimDef_c"],
        "moHoleTableDefs_c": KAnnotTableRules["moHoleTableDefs_c"],
        "moLabelDefs_c": KLabelAnnotationFields["moLabelDefs_c"],
        "moLengthUserUnits_c": KUnitFields["moLengthUserUnits_c"],
        "moLightFeature_c.FUN_4bc0b030": KLightFields["moLightFeature_c.FUN_4bc0b030"],
        "moLinearDimDef_c": KAnnotDimRules["moLinearDimDef_c"],
        "moLinearMotorUnits_c": KUnitFields["moLinearMotorUnits_c"],
        "moMassPropCache_c.Serialize": KMassCacheFields,
        "moMassProp_c": KMassPropFields,
        "moMaterial_c": KPartMatFields["moMaterial_c"],
        "moMiscLabelData_c": KLabelAnnotationFields["moMiscLabelData_c"],
        "moModelFeature_c": KLightFields["moModelFeature_c"],
        "moModel_c.FUN_4c17aa00": KModelLwRules["moModel_c.FUN_4c17aa00"],
        "moModel_c.FUN_4c210610": KModelResRules["moModel_c.FUN_4c210610"],
        "moModel_c.FUN_4c216d80": KModelResRules["moModel_c.FUN_4c216d80"],
        "moModel_c.FUN_4c22ec20": KModelResRules["moModel_c.FUN_4c22ec20"],
        "moModel_c.FUN_4c22ec80": KModelLwRules["moModel_c.FUN_4c22ec80"],
        "moModel_c.FUN_4c234150": KModelResRules["moModel_c.FUN_4c234150"],
        "moNodeList_c.Serialize": KConceptFields["moNodeList_c.Serialize"],
        "moNodeName_c": KLightFields["moNodeName_c"],
        "moNode_c.SerializeLWData": KFeatureFields["moNode_c.SerializeLWData"],
        "moNode_c.SerializeNode": KFeatureFields["moNode_c.SerializeNode"],
        "moNoteDataHelper_c": KAnnotHelpRules["moNoteDataHelper_c"],
        "moNoteDefs_c": KBaseAnnotationFields["moNoteDefs_c"],
        "moNumberUserUnits_c": KUnitFields["moNumberUserUnits_c"],
        "moOrdinateDimDef_c": KAnnotDimRules["moOrdinateDimDef_c"],
        "moOrthoLabelData_c": KLabelAnnotationFields["moOrthoLabelData_c"],
        "moPMarkRecord_c": KRecordFields["moPMarkRecord_c"],
        "moParameter_c.FUN_4c17a330": KPartMatFields["moParameter_c.FUN_4c17a330"],
        "moPart_c": KPartRootRules["moPart_c"],
        "moPart_c.FUN_4c2309d0": KPartRootRules["moPart_c.FUN_4c2309d0"],
        "moPart_c.FUN_4c2378b0": KPartRootRules["moPart_c.FUN_4c2378b0"],
        "moPowerUnits_c": KUnitFields["moPowerUnits_c"],
        "moPrtExplViewManager_c": KOwnerFields["moPrtExplViewManager_c"],
        "moPunchTableDefs_c": KAnnotTableRules["moPunchTableDefs_c"],
        "moRadialDimDef_c": KAnnotDimRules["moRadialDimDef_c"],
        "moRefIdToSketchBlockListMap_c.FUN_4c9080f0": KOwnerFields[
            "moRefIdToSketchBlockListMap_c.FUN_4c9080f0"
        ],
        "moRelMgr_c": KRelMgrFields["moRelMgr_c"],
        "moRevCloudDefs_c": KBaseAnnotationFields["moRevCloudDefs_c"],
        "moRevisionTableDefs_c": KAnnotTableRules["moRevisionTableDefs_c"],
        "moRotaryMotorUnits_c": KUnitFields["moRotaryMotorUnits_c"],
        "moSFDataHelper_c": KFinishFields["moSFDataHelper_c"],
        "moSFDefs_c": KBaseAnnotationFields["moSFDefs_c"],
        "moSectionLabelData_c": KLabelAnnotationFields["moSectionLabelData_c"],
        "moSheetMetalMaster_c": KPartFeatureRules["moSheetMetalMaster_c"],
        "moSketchBlockMgr_c": KOwnerFields["moSketchBlockMgr_c"],
        "moSpringConstantUnits_c": KUnitFields["moSpringConstantUnits_c"],
        "moStressUnits_c": KUnitFields["moStressUnits_c"],
        "moSwiftGtsOptions_c": KPartOptionRules["moSwiftGtsOptions_c"],
        "moTableDefs_c": KAnnotTableRules["moTableDefs_c"],
        "moTimeUnits_c": KUnitFields["moTimeUnits_c"],
        "moTitleBlockTableDefs_c": KAnnotTableRules["moTitleBlockTableDefs_c"],
        "moTransRefPlaneData_c": KPartRecordRules["moTransRefPlaneData_c"],
        "moUnitComponent_c": KPartRecordRules["moUnitComponent_c"],
        "moUnitSysUnits_c": KUnitFields["moUnitSysUnits_c"],
        "moUnitsTable_c": KUnitFields["moUnitsTable_c"],
        "moUserProperty_c.restore": KLightFields["moUserProperty_c.restore"],
        "moUserUnits_c.Serialize": KUnitFields["moUserUnits_c.Serialize"],
        "moViewLocationLabelDefs_c": KBaseAnnotationFields["moViewLocationLabelDefs_c"],
        "moView_c": KViewFields["moView_c"],
        "moVisProp_c": KFeatureFields["moVisProp_c"],
        "moVisualProperties_c": KPartVisualRules["moVisualProperties_c"],
        "moVisualProperties_c.restore": KPartVisualRules[
            "moVisualProperties_c.restore"
        ],
        "moWeldDataHelper_c": KAnnotHelpRules["moWeldDataHelper_c"],
        "moWeldDefs_c": KBaseAnnotationFields["moWeldDefs_c"],
        "moWeldTableDefs_c": KAnnotTableRules["moWeldTableDefs_c"],
        "rf.suObList": KConceptFields["rf.suObList"],
        "suObList": KObListFields,
        "su_CMapStringToOb.Serialize": KPartRecordRules["su_CMapStringToOb.Serialize"],
        "su_CMapWordToOb.Serialize": KOwnerFields["su_CMapWordToOb.Serialize"],
        "su_CObArray": KContainerFields["su_CObArray"],
        "su_CStringArray": KContainerFields["su_CStringArray"],
        "uiLFConfig_c": KFontFields["uiLFConfig_c"],
        "uoDSPBRProperties_c.restore": KPartPbrRules["uoDSPBRProperties_c.restore"],
        "uoMaterialProperties.restore": KPartVisualRules[
            "uoMaterialProperties.restore"
        ],
        "uoModelData_c": KPartMatFields["uoModelData_c"],
        "uoRVAppearanceProperties.restore": KPartVisualRules[
            "uoRVAppearanceProperties.restore"
        ],
        "utCharFormat_c": KFinishFields["utCharFormat_c"],
        "utLineWidthPrintData_c": KFormatAnnotationFields["utLineWidthPrintData_c"],
        "utLineWidth_c.Serialize.2.0": KFontFields["utLineWidth_c.Serialize.2.0"],
        "utLineWidth_c.Serialize0": KMaterialFields["utLineWidth_c.Serialize0"],
        "utLineWidth_c.Serialize2": KFeatureFields["utLineWidth_c.Serialize2"],
    }
)
