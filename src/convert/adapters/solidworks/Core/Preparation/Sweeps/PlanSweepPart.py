from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepLabels import (
    SweepLabels,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.CheckSwDoc import CheckSwDoc
from convert.adapters.solidworks.Core.Preparation.Sweeps.ReadSwDrivers import (
    FindSwDrivers,
    ReadSwDensity,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.ReadSwProfiles import (
    ReadSwProfiles,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.ReadSwSketches import (
    ReadSwPath,
    ReadSwSection,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent
from interchange.document.Models.DocumentModel import CadDocument


# project a complete ordinary neutral sweep through the actual typed section and path before any archive allocation
def PlanSweepPart(
    DocumentValue: CadDocument, TargetValue: SelfFileInput
) -> SweepIntent:
    if type(DocumentValue) is not CadDocument:
        raise TypeError("sweep planning requires a real neutral CadDocument")
    NameValue = ReadStyleText(
        DocumentValue.metadata.get("name"), "neutral sweep part name"
    )
    LabelsValue = SweepLabels(NameValue)
    CheckSwDoc(DocumentValue, LabelsValue)
    SectionValue, PathValue = ReadSwProfiles(DocumentValue, LabelsValue)
    SectionDrive, PathDrive, DensityDrive = FindSwDrivers(
        DocumentValue, SectionValue, PathValue
    )
    PlatformMath = DocumentValue.metadata.get("solidworks_platform_view_math", False)
    if type(PlatformMath) is not bool:
        raise ValueError("sweep view arithmetic selection must be boolean")
    return SweepIntent(
        NameValue,
        ReadSwSection(SectionValue, SectionDrive),
        ReadSwPath(PathValue, PathDrive),
        ReadSwDensity(DocumentValue, DensityDrive),
        TargetValue,
        PlatformViewMath=PlatformMath,
    )
