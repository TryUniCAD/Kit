from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import (
    HistoryInput,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Archive.Construction.System.SystemInput import (
    SystemInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)


# complete part construction needs explicit presentation target and provenance inputs beside the actual portable document semantics
@DataClass(frozen=True, slots=True)
class PartBuildInput:
    StyleValue: StyleInput
    DocumentUnits: UnitInput
    AnalysisUnits: UnitInput
    SystemValue: SystemInput
    TargetValue: FeatureTarget
    HeaderValue: HeaderInput
    HistoryValue: HistoryInput
    DefinitionValue: ModelDefInput
    OutputValue: SelfFileInput
    HatchName: str
    ManagerName: str
    DensityValue: float
    DesignIntent: bool
    SelectedLeader: int
    PropertiesValue: PartTextInput | None = None
