from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblySysIn import (
    AssemblySysIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.AsmVocabulary import (
    KAsmFolders,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from interchange.geometry.Models.SupportPlane import SupportPlane


# assembly defaults must preserve documented native role order while retaining actual principal and mate group names
def DefaultAsmTree(
    RecipeValue: PartBuildInput,
    PlanesValue: Mapping[str, SupportPlane],
    GroupName: str,
    WrittenAt: int,
) -> AssemblySysIn:
    NamesValue = dict(RecipeValue.SystemValue.FolderValues)
    NamesValue["moLiveSectionFolder_c"] = "Live Section Planes"
    return AssemblySysIn(
        tuple((KindValue, NamesValue[KindValue]) for KindValue in KAsmFolders),
        tuple((AxisValue, PlanesValue[AxisValue].name) for AxisValue in "xyz"),
        RecipeValue.SystemValue.CabinetName,
        RecipeValue.SystemValue.OriginName,
        GroupName,
        WrittenAt,
    )
