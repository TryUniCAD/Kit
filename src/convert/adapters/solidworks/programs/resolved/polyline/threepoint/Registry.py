from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramComposer import BuildProgram
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Archive.SuCArchive.ReadClass import (
    KMethodProgram as KMethodA,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Archive.SuCArchive.WriteString import (
    KMethodProgram as KMethodB,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldarchiveu.Functions.MoGetModelnameFromPath import (
    KMethodProgram as KMethodC,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldarchiveu.MoSharedFileDefC.Serialize import (
    KMethodProgram as KMethodD,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmfcu.MoLineVizC.Serialize import (
    KMethodProgram as KMethodE,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmfcu.SuObArray.SerializePtr import (
    KMethodProgram as KMethodF,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmfcu.UtLineWidthC.Serialize import (
    KMethodProgram as KMethodG,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmgu.Functions.ReadOperator import (
    KMethodProgram as KMethodH,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmgu.MgMatrixC.Restore import (
    KMethodProgram as KMethodI,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmgu.MgPointC.Restore import (
    KMethodProgram as KMethodJ,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmgu.MgPointC.RestoreTwoD import (
    KMethodProgram as KMethodK,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmgu.MgVectorC.Restore import (
    KMethodProgram as KMethodL,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmgu.MgXformC.LinearComponent import (
    KMethodProgram as KMethodM,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmgu.MgXformC.Restore import (
    KMethodProgram as KMethodN,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.BentRefArr.Serialize import (
    KMethodProgram as KMethodO,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.DimensionC.Serialize import (
    KMethodProgram as KMethodP,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.Functions.MoLoadBodyFromArchive import (
    KMethodProgram as KMethodQ,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoArrowSizeC.Serialize import (
    KMethodProgram as KMethodR,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoBodyFeatureC.Serialize import (
    KMethodProgram as KMethodS,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoCompLoopC.Serialize import (
    KMethodProgram as KMethodT,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoCompRefC.Serialize import (
    KMethodProgram as KMethodU,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoConceptC.SerializeLWData import (
    KMethodProgram as KMethodV,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoDimPatternRegenStatusC.Serialize import (
    KMethodProgram as KMethodW,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoDimTextC.GetRuntimeClass import (
    KMethodProgram as KMethodX,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoDisplayDimC.SafeSetFeatureOwner import (
    KMethodProgram as KMethodY,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoDisplayItemC.Serialize import (
    KMethodProgram as KMethodZ,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoDynSurfIdArr.Serialize import (
    KMethodProgram as KMethodAA,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoEdgeSurfIdKeeperC.Serialize import (
    KMethodProgram as KMethodAB,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoEntVisPropC.Serialize import (
    KMethodProgram as KMethodAC,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KMethodProgram as KMethodAD,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoFeatureC.Serialize import (
    KMethodProgram as KMethodAE,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoFolderC.Serialize import (
    KMethodProgram as KMethodAF,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoFtrFolderC.Serialize import (
    KMethodProgram as KMethodAG,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoMateBeltDimC.GetThisClass import (
    KMethodProgram as KMethodAH,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoModelFeatureC.Serialize import (
    KMethodProgram as KMethodAI,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoNodeC.SerializeLWData import (
    KMethodProgram as KMethodAJ,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoPSMeshToleranceHandlerC.Serialize import (
    KMethodProgram as KMethodAK,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoPTSRefPlnDataC.Serialize import (
    KMethodProgram as KMethodAL,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoRefPlnDataC.SerializePlaneData import (
    KMethodProgram as KMethodAM,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoReferenceCurveC.Serialize import (
    KMethodProgram as KMethodAN,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoSMAndFPFeatIdPair.Serialize import (
    KMethodProgram as KMethodAO,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoSelectionSetNodeC.GetRuntimeClass import (
    KMethodProgram as KMethodAP,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoSubFavoriteFolderC.GetThisClass import (
    KMethodProgram as KMethodAQ,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoSwiftFRC.GetThisClass import (
    KMethodProgram as KMethodAR,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoThreedViewC.Serialize import (
    KMethodProgram as KMethodAS,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoVectorParameterC.GetThisClass import (
    KMethodProgram as KMethodAT,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoVisPropC.Serialize import (
    KMethodProgram as KMethodAU,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoVisualOverlayObjectC.GetThisClass import (
    KMethodProgram as KMethodAV,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoWeldFavoriteC.GetRuntimeClass import (
    KMethodProgram as KMethodAW,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.MoXformStockC.GetThisClass import (
    KMethodProgram as KMethodAX,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.SgDim.Serialize import (
    KMethodProgram as KMethodAY,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.SgEntHandle.Serialize import (
    KMethodProgram as KMethodAZ,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.SgLogDim.Serialize import (
    KMethodProgram as KMethodBA,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.SgLogGroupDim.Serialize import (
    KMethodProgram as KMethodBB,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.SgSketch.IPostLoad import (
    KMethodProgram as KMethodBC,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.SgSketch.LoadSketchInPlace import (
    KMethodProgram as KMethodBD,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KMethodProgram as KMethodBE,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.SgSketch.Serialize import (
    KMethodProgram as KMethodBF,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KMethodProgram as KMethodBG,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Sldmodu.StructConnectionCutSurfIdRepC.GetThisClass import (
    KMethodProgram as KMethodBH,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Swccu.Functions.ReadOperator import (
    KMethodProgram as KMethodBI,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Swccu.SuCArchive.ReadCount import (
    KMethodProgram as KMethodBJ,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Swccu.SuCArchive.ReadObject import (
    KMethodProgram as KMethodBK,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Synthetic.ArchiveContinuationBase import (
    KMethodProgram as KMethodBL,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Synthetic.BodyChooserBoundingBoxes import (
    KMethodProgram as KMethodBM,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Synthetic.DisplayDimensionDerivedScalars import (
    KMethodProgram as KMethodBN,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Synthetic.DisplayDimensionDirectSlots import (
    KMethodProgram as KMethodBO,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Synthetic.DisplayDimensionIndices import (
    KMethodProgram as KMethodBP,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Methods.Synthetic.SketchChainEntityIndices import (
    KMethodProgram as KMethodBQ,
)

KMethodPrograms = (
    KMethodA,
    KMethodB,
    KMethodC,
    KMethodD,
    KMethodE,
    KMethodF,
    KMethodG,
    KMethodH,
    KMethodI,
    KMethodJ,
    KMethodK,
    KMethodL,
    KMethodM,
    KMethodN,
    KMethodO,
    KMethodP,
    KMethodQ,
    KMethodR,
    KMethodS,
    KMethodT,
    KMethodU,
    KMethodV,
    KMethodW,
    KMethodX,
    KMethodY,
    KMethodZ,
    KMethodAA,
    KMethodAB,
    KMethodAC,
    KMethodAD,
    KMethodAE,
    KMethodAF,
    KMethodAG,
    KMethodAH,
    KMethodAI,
    KMethodAJ,
    KMethodAK,
    KMethodAL,
    KMethodAM,
    KMethodAN,
    KMethodAO,
    KMethodAP,
    KMethodAQ,
    KMethodAR,
    KMethodAS,
    KMethodAT,
    KMethodAU,
    KMethodAV,
    KMethodAW,
    KMethodAX,
    KMethodAY,
    KMethodAZ,
    KMethodBA,
    KMethodBB,
    KMethodBC,
    KMethodBD,
    KMethodBE,
    KMethodBF,
    KMethodBG,
    KMethodBH,
    KMethodBI,
    KMethodBJ,
    KMethodBK,
    KMethodBL,
    KMethodBM,
    KMethodBN,
    KMethodBO,
    KMethodBP,
    KMethodBQ,
)
KFieldOwners, KResolvedOps = BuildProgram(
    KMethodPrograms,
    "ResolvedFeatures",
)

__all__ = [
    "KFieldOwners",
    "KResolvedOps",
    "KMethodPrograms",
    "FieldOwners",
    "ResolvedOps",
]

FieldOwners = KFieldOwners

ResolvedOps = KResolvedOps
