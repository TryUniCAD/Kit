from __future__ import annotations

from tests.Convert.Solidworks.Research.Model.ModelPaths import KImports
from tests.Convert.Solidworks.Research.Model.ModelGuard import KGuard
from tests.Convert.Solidworks.Research.Model.ModelNative import KNative
from tests.Convert.Solidworks.Research.Model.ModelBuilders import KBuilders
from tests.Convert.Solidworks.Research.Model.ModelCodec import KCodec
from tests.Convert.Solidworks.Research.Model.BaseImports import KBaseImports
from tests.Convert.Solidworks.Research.Model.ModelComponents import KBuild
from tests.Convert.Solidworks.Research.Model.ModelPlanes import KPlanes
from tests.Convert.Solidworks.Research.Model.ModelFolders import KFolders
from tests.Convert.Solidworks.Research.Model.ModelCabinet import KAnnotations
from tests.Convert.Solidworks.Research.Model.BaseStyles import KBaseStyles
from tests.Convert.Solidworks.Research.Model.BaseGraph import KBaseGraph
from tests.Convert.Solidworks.Research.Model.BaseLifecycle import KBaseLifecycle
from tests.Convert.Solidworks.Research.Model.BaseStreams import KBaseStreams
from tests.Convert.Solidworks.Research.Model.References.Build import KReferences
from tests.Convert.Solidworks.Research.Model.BaseRevision import KBaseRevision
from tests.Convert.Solidworks.Research.Model.BaseHeader import KBaseHeader
from tests.Convert.Solidworks.Research.Model.ModelContainer import KContainer
from tests.Convert.Solidworks.Research.Model.BaseLoad import KBaseLoad
from tests.Convert.Solidworks.Research.Model.BaseAliases import KBaseAliases
from tests.Convert.Solidworks.Research.Model.References.Load import KReferenceLoad
from tests.Convert.Solidworks.Research.Model.BaseCheck import KBaseCheck
from tests.Convert.Solidworks.Research.Model.ModelCheck import KCheck
from tests.Convert.Solidworks.Research.Model.ModelMetrics import KMetrics
from tests.Convert.Solidworks.Research.Model.ModelReport import KReport
from tests.Convert.Solidworks.Research.Model.BaseMetrics import KBaseMetrics

# one assembled child program keeps construction behind the same audit and isolation boundary
KProgram = (
    KImports
    + KGuard
    + KNative
    + KBuilders
    + KBaseImports
    + KCodec
    + KBuild
    + KPlanes
    + KFolders
    + KAnnotations
    + KBaseStyles
    + KBaseGraph
    + KBaseLifecycle
    + KBaseStreams
    + KReferences
    + KBaseRevision
    + KBaseHeader
    + KContainer
    + KBaseLoad
    + KBaseAliases
    + KBaseCheck
    + KReferenceLoad
    + KCheck
    + KMetrics
    + KBaseMetrics
    + KReport
)
