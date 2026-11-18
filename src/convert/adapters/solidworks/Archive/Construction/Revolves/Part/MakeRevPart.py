from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevFeatMut import (
    MakeRevFeatMut,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import (
    ProjectRevolve,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.EmitRevStreams import (
    EmitRevStreams,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.RevolvePart import (
    RevolvePart,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Sketch.MakeRevProfMut import (
    MakeRevProfMut,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from interchange.document.Models.DocumentModel import CadDocument


# the measured internal revolve constructor must synthesize every stream from neutral semantics and explicit presentation without registering public support
def MakeRevPart(DocumentValue: CadDocument, InputValue: PartBuildInput) -> RevolvePart:
    PlanValue = ProjectRevolve(DocumentValue)
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    if (
        InputValue.PropertiesValue is not None
        or InputValue.DocumentUnits.AngleUnit != "degree"
    ):
        raise ValueError(
            "ordinary revolve construction requires degree presentation and no optional properties"
        )
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(InputValue, PlanValue, Allocator)
    ProfileValue, AxisValue = MakeRevProfMut(
        SystemValue, InputValue, PlanValue, Allocator
    )
    FeatureValue, Reference, EndValue, AngleValue = MakeRevFeatMut(
        SystemValue, ProfileValue, AxisValue, InputValue, PlanValue, Allocator
    )
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    HeadersValue = MakePartHeaders(SystemValue, InputValue, Allocator)
    Definition = MakePartDef(InputValue.DefinitionValue, InputValue.DensityValue)
    FeatureValues = (
        *SystemValue.FeatureValues,
        ProfileValue.ProfileValue,
        FeatureValue,
    )
    StreamsValue, ConfigValue, ResolvedValue = EmitRevStreams(
        SystemValue, FeatureValues, HeadersValue, Definition, InputValue, PlanValue
    )
    return RevolvePart(
        SystemValue,
        ProfileValue,
        FeatureValue,
        Reference,
        EndValue,
        AngleValue,
        HeadersValue,
        Definition,
        ConfigValue,
        ResolvedValue,
        StreamsValue,
        BuildSldprt(StreamsValue, FormatVersion=4),
        PlanValue,
        InputValue,
    )
