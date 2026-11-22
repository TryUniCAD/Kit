from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ValueKind
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordParameter import Parameter


# the two editable sketch dimensions and the unassigned physical density are separate model owners
def FindSwDrivers(
    DocumentValue: CadDocument, SectionValue: Sketch, PathValue: Sketch
) -> tuple[Parameter, Parameter, Parameter]:
    if len(SectionValue.parameter_ids) != 1 or len(PathValue.parameter_ids) != 1:
        raise ValueError("sweep sketches require their own independent D1 driver")
    SectionId, PathId = SectionValue.parameter_ids[0], PathValue.parameter_ids[0]
    ParamValues = {Value.id: Value for Value in DocumentValue.parameters}
    if SectionId == PathId or not {SectionId, PathId} <= ParamValues.keys():
        raise ValueError("sweep sketches require distinct actual D1 parameters")
    (DensityId,) = ParamValues.keys() - {SectionId, PathId}
    SectionDrive, PathDrive, DensityDrive = (
        ParamValues[ParamId] for ParamId in (SectionId, PathId, DensityId)
    )
    CheckCircDrive(SectionDrive, SectionValue.id, "D1")
    CheckCircDrive(PathDrive, PathValue.id, "D1")
    return SectionDrive, PathDrive, DensityDrive


# preserve both unit spelling and active driving literal interpretation before converting scales
def ReadSwLength(DriverValue: Parameter) -> float:
    ParameterValue = DriverValue.value
    if ParameterValue.kind != ValueKind.KLength or ParameterValue.unit != "mm":
        raise ValueError("sweep D1 requires an explicit millimetre length")
    return RequireScalar(ParameterValue.value) / 1000.0


# scalar density must belong to the actual sole result and carry no unresolved material selection
def ReadSwDensity(DocumentValue: CadDocument, DriverValue: Parameter) -> float:
    BodyValue = DocumentValue.bodies[0]
    StepValue = DocumentValue.feature_timeline[0]
    if (
        BodyValue.name != StepValue.name
        or BodyValue.final_feature_id != StepValue.id
        or BodyValue.material_id is not None
        or BodyValue.attributes
    ):
        raise ValueError(
            "sweep requires its actual unassigned body owned by the first creator"
        )
    CheckCircDrive(DriverValue, BodyValue.id, "Density")
    if (
        DriverValue.value.kind != ValueKind.KQuantity
        or DriverValue.value.unit != "kg/m3"
    ):
        raise ValueError("sweep density requires an explicit kg/m3 quantity")
    return RequireScalar(DriverValue.value.value)
