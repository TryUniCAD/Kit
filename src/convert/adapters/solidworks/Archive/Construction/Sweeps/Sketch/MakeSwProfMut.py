from convert.adapters.solidworks.Archive.Construction.Circles.AddCircDimMut import (
    AddCircDimMut,
)
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircleFeat import (
    MakeCircleFeat,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Profile.BeginProfileMut import (
    BeginProfileMut,
)
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileData import (
    MakeProfileData,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import (
    MakeSketchSeed,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.BindSwDimsMut import (
    BindSwDimsMut,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.MakePathArcMut import (
    MakePathArcMut,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.MakePathDimMut import (
    MakePathDimMut,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.SweepProfiles import (
    SweepProfiles,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepLabels import (
    SweepLabels,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent


# the solid sweep uses distinct right and front sketches before constructing its feature
def MakeSwProfMut(
    SystemValue: PartSystem,
    InputValue: PartBuildInput,
    Allocator: PersistentIds,
    IntentValue: SweepIntent,
    LabelsValue: SweepLabels,
) -> SweepProfiles:
    PlaneValues = SystemValue.SystemValues.PlaneValues
    TargetValue = InputValue.TargetValue
    CircleValue = IntentValue.SectionValue
    SectionValue = MakeCircleFeat(
        LabelsValue.SectionName,
        SystemValue.RootValue,
        PlaneValues["x"],
        "x",
        CircleInput(
            (CircleValue.Center.XCoord, CircleValue.Center.YCoord),
            CircleValue.Radius,
            TargetValue.FileVersion,
        ),
        TargetValue,
        Allocator,
    )
    DiameterValue = AddCircDimMut(
        SectionValue,
        (0.012, 0.012),
        True,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
        Allocator,
    )
    PathValue, SupportValue, FrameValue = BeginProfileMut(
        LabelsValue.SketchName,
        SystemValue.RootValue,
        PlaneValues["z"],
        "z",
        TargetValue,
        Allocator,
    )
    SketchValue = MakeSketchSeed(PathValue)
    PathValue.FieldsValue.update(MakeProfileData(SketchValue, SupportValue, FrameValue))
    ArcValue, PointValues = MakePathArcMut(SketchValue, IntentValue.PathValue)
    RadiusValue = MakePathDimMut(
        PathValue, FrameValue, SketchValue, ArcValue, PointValues, InputValue, Allocator
    )
    BindSwDimsMut(SketchValue, ArcValue, PointValues, RadiusValue)
    return SweepProfiles(
        SectionValue.ProfileValue, PathValue, DiameterValue, RadiusValue
    )
