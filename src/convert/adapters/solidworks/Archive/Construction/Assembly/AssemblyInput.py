from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblySysIn import (
    AssemblySysIn,
)
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import (
    HistoryInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)


# complete assembly construction needs explicit authored presentation provenance target and system semantics beside its actual generated child
@DataClass(frozen=True, slots=True)
class AssemblyInput:
    NameValue: str
    ConfigName: str
    ManagerName: str
    StyleValue: StyleInput
    DocumentUnits: UnitInput
    SystemValue: AssemblySysIn
    TargetValue: FeatureTarget
    HeaderValue: HeaderInput
    HistoryValue: HistoryInput
    DefinitionValue: ModelDefInput
    OutputValue: SelfFileInput
    SavePartValues: Mapping[str, bool | int | float]
    ModelName: str | None = None
