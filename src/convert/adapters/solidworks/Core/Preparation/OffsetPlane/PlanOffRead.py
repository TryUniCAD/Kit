from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetInput import (
    OffsetInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.PlanOffPart import (
    PlanOffPart,
)
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.ProjectOffPad import (
    ProjectOffPad,
)
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.ProjectOffRef import (
    ProjectOffRef,
)
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.ProjectOffSk import (
    ProjectOffSk,
)
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.ReadOffDrive import (
    ReadOffDrive,
)
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.ReadOffSteps import (
    ReadOffSteps,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# extraction is restricted to construction inputs and the caller verifies the untouched complete source before publication
def PlanOffRead(
    DocumentValue: CadDocument, NameValue: str
) -> tuple[CirclePlan, OffsetInput]:
    DocumentValue.assert_valid()
    (Sketch,) = DocumentValue.sketches
    (BodyValue,) = DocumentValue.bodies
    (Config,) = DocumentValue.configurations
    Datum, Profile, BossStep = ReadOffSteps(DocumentValue, Sketch)
    Drivers = {Param.id: Param for Param in DocumentValue.parameters}
    (OffsetId,) = Datum.parameter_ids
    (RadiusId,) = Profile.parameter_ids
    (DepthId,) = BossStep.parameter_ids
    if set(Drivers) != {OffsetId, RadiusId, DepthId} or len(Drivers) != 3:
        raise ValueError(
            "SOLIDWORKS offset readback requires three distinct driving parameters"
        )
    Distance = ReadOffDrive(Drivers[OffsetId], Datum.id, "offset")
    Radius = ReadOffDrive(Drivers[RadiusId], Profile.id, "length", IsRadial=True)
    Depth = ReadOffDrive(Drivers[DepthId], BossStep.id, "length")
    Offset, BasePlane, Carrier = ProjectOffRef(
        DocumentValue, Datum, Drivers[OffsetId], Distance
    )
    CreateStep = ProjectOffPad(BossStep, Offset.id, Drivers[DepthId], Depth)
    RadiusMetres = RequireScalar(Radius.value.value)
    InputValue = ReplaceValue(
        DocumentValue,
        source=ReplaceValue(DocumentValue.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(Config, attributes=FreezeMapping()),),
        parameters=(Distance, ReplaceValue(Radius, owner_id=Sketch.id), Depth),
        support_planes=(BasePlane, Carrier),
        sketches=(ProjectOffSk(Sketch, Radius.id, RadiusMetres),),
        feature_timeline=(Offset, CreateStep),
        selections=(),
        bodies=(
            ReplaceValue(
                BodyValue,
                name=CreateStep.name,
                provenance=None,
                attributes=FreezeMapping(),
                topology=TopologyCounts(),
            ),
        ),
        diagnostics=(),
        metadata=FreezeMapping({"name": NameValue}),
        capabilities=frozenset(),
        brep=None,
    )
    PlanValue, DatumValue = PlanOffPart(InputValue)
    return (
        ReplaceValue(
            PlanValue,
            CircleValue=ReplaceValue(PlanValue.CircleValue, RadiusValue=RadiusMetres),
        ),
        DatumValue,
    )
