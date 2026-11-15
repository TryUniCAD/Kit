from __future__ import annotations

from tests.convert.solidworks.research.Model.ModelPaths import KImports
from tests.convert.solidworks.research.Model.ModelGuard import KGuard
from tests.convert.solidworks.research.Model.ModelNative import KNative
from tests.convert.solidworks.research.Model.ModelBuilders import KBuilders
from tests.convert.solidworks.research.Model.ModelCodec import KCodec
from tests.convert.solidworks.research.Model.BaseImports import KBaseImports
from tests.convert.solidworks.research.Model.ModelComponents import KBuild
from tests.convert.solidworks.research.Model.ModelPlanes import KPlanes
from tests.convert.solidworks.research.Model.ModelFolders import KFolders
from tests.convert.solidworks.research.Model.ModelCabinet import KAnnotations
from tests.convert.solidworks.research.Model.BaseStyles import KBaseStyles
from tests.convert.solidworks.research.Model.BaseGraph import KBaseGraph
from tests.convert.solidworks.research.Model.BaseLifecycle import KBaseLifecycle
from tests.convert.solidworks.research.Model.BaseStreams import KBaseStreams
from tests.convert.solidworks.research.Model.BaseRevision import KBaseRevision
from tests.convert.solidworks.research.Model.BaseHeader import KBaseHeader
from tests.convert.solidworks.research.Model.ModelContainer import KContainer
from tests.convert.solidworks.research.Model.BaseLoad import KBaseLoad
from tests.convert.solidworks.research.Model.BaseAliases import KBaseAliases
from tests.convert.solidworks.research.Model.BaseCheck import KBaseCheck
from tests.convert.solidworks.research.Model.ModelCheck import KCheck
from tests.convert.solidworks.research.Model.ModelMetrics import KMetrics
from tests.convert.solidworks.research.Model.ModelReport import KReport
from tests.convert.solidworks.research.Model.BaseMetrics import KBaseMetrics

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
    + KBaseRevision
    + KBaseHeader
    + KContainer
    + KBaseLoad
    + KBaseAliases
    + KBaseCheck
    + KCheck
    + KMetrics
    + KBaseMetrics
    + KReport
)
