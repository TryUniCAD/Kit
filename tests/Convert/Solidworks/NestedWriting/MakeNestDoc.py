from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.document.Models.DocumentModel import (
    AssemblyData,
    CadDocument,
    ComponentDoc,
)
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc


# the authored hierarchy places one shared module twice through different rigid frames
def MakeNestDoc(
    RingPoints: tuple[tuple[float, float], ...] = (
        (0.0, 0.0),
        (17.0, 0.0),
        (17.0, 9.0),
        (0.0, 9.0),
    ),
) -> CadDocument:
    PlateValue = MakePlainDoc("QueuePlate", RingPoints, 7.5)
    PlateConfig = PlateValue.configurations[0]
    RootConfig = Configuration("config/frame", "Project setup", active=True)
    ModuleConfig = Configuration("config/module", "Module setup", active=True)
    Definitions = (
        ComponentDef(
            "def/frame",
            "QueueFrame",
            "assembly",
            configuration_name=RootConfig.name,
            configuration_id=RootConfig.id,
        ),
        ComponentDef(
            "def/module",
            "QueueModule",
            "assembly",
            configuration_name=ModuleConfig.name,
            configuration_id=ModuleConfig.id,
        ),
        ComponentDef(
            "def/plate",
            "QueuePlate",
            "part",
            document_id="doc/plate",
            configuration_name=PlateConfig.name,
            configuration_id=PlateConfig.id,
            body_ids=tuple(BodyValue.id for BodyValue in PlateValue.bodies),
        ),
    )
    return CadDocument(
        CadSource("kit-neutral", "<authored-in-memory>", "0" * 64),
        (RootConfig,),
        (),
        MakeNestPlanes(),
        (),
        (),
        (),
        (),
        metadata={"name": "QueueFrame"},
        assembly=AssemblyData(
            "def/frame",
            Definitions,
            MakeNestPoses(Definitions),
            (ComponentDoc("doc/plate", PlateValue),),
        ),
    )


# explicit canonical witness frames keep the three datum roles independent of the assembly writer
def MakeNestPlanes() -> tuple[SupportPlane, ...]:
    AxisX = SpaceVector(1.0, 0.0, 0.0)
    AxisY = SpaceVector(0.0, 1.0, 0.0)
    NegAxisZ = SpaceVector(0.0, 0.0, -1.0)
    OriginValue = SpaceVector(0.0, 0.0, 0.0)
    return (
        SupportPlane("plane/front", "Front Plane", Transform()),
        SupportPlane(
            "plane/right", "Right Plane", Transform(OriginValue, NegAxisZ, AxisY, AxisX)
        ),
        SupportPlane(
            "plane/top", "Top Plane", Transform(OriginValue, AxisX, NegAxisZ, AxisY)
        ),
    )


# the two placements of the module refer to the same native file and keep separate transforms
def MakeNestPoses(Definitions: tuple[ComponentDef, ...]) -> tuple[ComponentInst, ...]:
    RootValue, ModuleValue, PlateValue = Definitions
    RotateShift = TransformMatrix(
        (
            0.0,
            -1.0,
            0.0,
            23.0,
            1.0,
            0.0,
            0.0,
            14.0,
            0.0,
            0.0,
            1.0,
            8.0,
            0.0,
            0.0,
            0.0,
            1.0,
        )
    )
    return (
        ComponentInst(
            "inst/plate",
            "QueuePlate-1",
            PlateValue.id,
            ModuleValue.id,
            configuration_name=PlateValue.configuration_name,
            configuration_id=PlateValue.configuration_id,
        ),
        ComponentInst(
            "inst/module1",
            "QueueModule-1",
            ModuleValue.id,
            RootValue.id,
            configuration_name=ModuleValue.configuration_name,
            configuration_id=ModuleValue.configuration_id,
        ),
        ComponentInst(
            "inst/module2",
            "QueueModule-2",
            ModuleValue.id,
            RootValue.id,
            RotateShift,
            order=1,
            configuration_name=ModuleValue.configuration_name,
            configuration_id=ModuleValue.configuration_id,
        ),
    )
