from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.BodyScope.SelectedStock import (
    SelectedStock,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceAxis import (
    SourceAxis,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceLine import (
    SourceLine,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourcePlane import (
    SourcePlane,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceRefs import (
    SourceRefs,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)


# generation receives only typed portable geometry and ownership while native source state remains in a separate envelope
@DataClass(frozen=True, slots=True)
class ThruOwnerInput:
    ShapeValue: ThroughPartSpec
    ScopeValue: SelectedStock
    PlaneValues: tuple[SourcePlane, ...]
    LineValues: tuple[SourceLine, ...]
    AxisValues: tuple[SourceAxis, ...]
    RefsValue: SourceRefs
    UnitValue: str
