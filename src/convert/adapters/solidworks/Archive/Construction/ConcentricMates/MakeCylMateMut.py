from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Assembly.RecordMateMut import (
    RecordMateMut,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CheckCylPlace import (
    CheckCylPlace,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CheckCylPose import (
    CheckCylPose,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateCtx import (
    CylMateCtx,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateIn import (
    CylMateIn,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.GetCylAxes import (
    GetCylAxes,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylActive import (
    MakeCylActive,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylFile import (
    MakeCylFile,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylPlaces import (
    MakeCylPlaces,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylSupport import (
    MakeCylSupport,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.PutCylMateMut import (
    PutCylMateMut,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.ReadMintedCyl import (
    ReadMintedCyl,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the mate is constructed only after validating its actual selected faces and coaxial occurrence frames
def MakeCylMateMut(
    Context: CylMateCtx,
    References: tuple[ArchiveNode, ArchiveNode],
    FramesValue: tuple[PlaneFrame, PlaneFrame],
    FaceTag: int,
    IntentValue: CylMateIn,
) -> ArchiveNode:
    if (
        len(CastValue(tuple[object, ...], References)) != 2
        or References[0] is References[1]
        or len(CastValue(tuple[object, ...], FramesValue)) != 2
        or type(IntentValue.FixedIndex) is not int
        or IntentValue.FixedIndex not in (0, 1)
        or type(IntentValue.AlignmentCode) is not int
        or IntentValue.AlignmentCode not in (1, 2)
        or type(IntentValue.RotationLocked) is not bool
    ):
        raise ValueError(
            "concentric mate requires two actual occurrences, explicit alignment and one fixed anchor"
        )
    for Reference, FrameValue in zip(References, FramesValue, strict=True):
        CheckCylPlace(Reference, FrameValue, Context.ChildValue)
    FaceValue = ReadMintedCyl(Context.ChildValue, FaceTag)
    AxesValue = GetCylAxes(FaceValue.AxisValue, IntentValue.LocalAxes)
    Places = MakeCylPlaces(References, FramesValue, AxesValue, FaceValue.OriginValue)
    CheckCylPose(*Places, IntentValue.AlignmentCode)
    FileValue = MakeCylFile(Context.ChildValue)
    Active = tuple(
        MakeCylActive(
            Context, FaceValue, Value, FileValue, IntentValue.LocalAxes is not None
        )
        for Value in Places
    )
    Support = tuple(MakeCylSupport(Context, FaceValue, Value) for Value in Places)
    MateValue = PutCylMateMut(Context, IntentValue, Active, Support)
    References[IntentValue.FixedIndex].FieldsValue["f408"] = 1
    RecordMateMut(
        Context.StateValue, Context.InputValue, MateValue, Context.HeadersValue
    )
    return MateValue
