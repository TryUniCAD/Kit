from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePart import (
    EllipsePart,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartKeys import (
    MakePartKeys,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt


# ellipse activation is limited to the resolved serializer while all ordinary part stream owners remain shared
def EmitEllipsePart(
    SystemValue: PartSystem,
    RootsValue: tuple[ArchiveNode, ...],
    HeadersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    InputValue: PartBuildInput,
    PlanValue: EllipsePlan,
) -> EllipsePart:
    KeywordsValue = MakePartKeys(SystemValue, RootsValue, InputValue, PlanValue)
    Definition = MakePartDef(InputValue.DefinitionValue, InputValue.DensityValue)
    StreamsValue, ConfigValue, ResolvedValue = EmitPartArchive(
        SystemValue,
        RootsValue,
        HeadersValue,
        Definition,
        InputValue,
        KeywordsValue,
        BodyMapFields={"n": 0, "fcd8": []},
        ReplayEllipses=True,
    )
    return EllipsePart(
        PlanValue,
        ConfigValue,
        ResolvedValue,
        StreamsValue,
        BuildSldprt(StreamsValue, FormatVersion=4),
    )
