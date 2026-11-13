from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec

KPartFeature: TypeAlias = (
    FilletSpec
    | ChamferSpec
    | ShellSpec
    | ExtrudeSpec
    | HoleSpec
    | PatternSpec
    | CircularSpec
    | MirrorSpec
    | PlaneSpec
    | AxisSpec
    | PointSpec
    | RevolveSpec
    | MoveSpec
    | OffsetSpec
    | DraftSpec
)
