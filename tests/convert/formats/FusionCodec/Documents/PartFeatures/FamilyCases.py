from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
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
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import (
    PlaneSpec,
)

KBlock = ExtrudeSpec(
    (
        LineCurve((0.0, 0.0), (40.0, 0.0)),
        LineCurve((40.0, 0.0), (40.0, 30.0)),
        LineCurve((40.0, 30.0), (0.0, 30.0)),
        LineCurve((0.0, 30.0), (0.0, 0.0)),
    ),
    20.0,
    "new",
    "one",
    0.0,
    "Base sketch",
    "Base extrude",
)
KPocket = ExtrudeSpec(
    (CircleCurve((8.0, 8.0), 3.0),),
    20.0,
    "cut",
    "one",
    0.0,
    "Pocket sketch",
    "Pocket extrude",
)
KSlot = ExtrudeSpec(
    (
        LineCurve((10.0, 19.0), (14.0, 19.0)),
        ArcCurve((14.0, 22.0), 3.0, -90.0, 180.0),
        LineCurve((14.0, 25.0), (10.0, 25.0)),
        ArcCurve((10.0, 22.0), 3.0, 90.0, 180.0),
    ),
    8.0,
    "cut",
    "one",
    0.0,
    "Slot sketch",
    "Slot pocket",
)
KDisc = ExtrudeSpec(
    (CircleCurve((0.0, 0.0), 20.0),),
    12.0,
    "new",
    "one",
    0.0,
    "Disc sketch",
    "Disc extrude",
)
KRing = ExtrudeSpec(
    (CircleCurve((12.0, 0.0), 3.0),),
    6.0,
    "cut",
    "one",
    0.0,
    "Pocket sketch",
    "Pocket extrude",
)
KFamilyCases: dict[str, tuple[tuple[KPartFeature, ...], float, int, int]] = {
    "HoleFlat": ((KBlock, HoleSpec((20.0, 15.0), 8.0, 10.0)), 23.497345, 8, 14),
    "HoleCounterbore": (
        (KBlock, HoleSpec((20.0, 15.0), 6.0, 0.0, 10.0, 4.0)),
        23.233451,
        9,
        16,
    ),
    "RectPattern": (
        (KBlock, KPocket, PatternSpec(1, 3, 12.0, 2, 14.0)),
        20.60708,
        12,
        24,
    ),
    "FeatureCircPattern": (
        (KBlock, KPocket, CircularSpec(1, 2, 40.0)),
        23.03561,
        9,
        20,
    ),
    "MirrorFeature": (
        (KBlock, KPocket, PlaneSpec(20.0, "yz"), MirrorSpec(1, 2)),
        22.869027,
        8,
        16,
    ),
    "PlaneOffset": ((KBlock, PlaneSpec(15.0, "xy")), 24.0, 6, 12),
    "MultiPocketPart": (
        (
            KBlock,
            KSlot,
            HoleSpec((8.0, 8.0), 4.0),
            PatternSpec(2, 2, 12.0, 1, 10.0),
            FilletSpec((40.0, 30.0), 3.0),
            PlaneSpec(20.0, "yz"),
            MirrorSpec(1, 5),
        ),
        22.622328,
        19,
        43,
    ),
    "MultiDiscPart": (
        (
            KDisc,
            KRing,
            CircularSpec(1, 4, 360.0),
            HoleSpec((0.0, 0.0), 8.0, 0.0, 14.0, 4.0),
        ),
        13.383185,
        14,
        14,
    ),
    "ChamferTwoDistances": (
        (KBlock, ChamferSpec((40.0, 30.0), 3.0, "Corner bevel", 2.0)),
        23.94,
        7,
        15,
    ),
    "ChamferDistanceAngle": (
        (KBlock, ChamferSpec((40.0, 30.0), 3.0, "Corner bevel", 0.0, 30.0)),
        23.948038,
        7,
        15,
    ),
}
KFamilyNames: dict[type[object], str] = {
    ExtrudeSpec: "DcExtrudeFeature",
    HoleSpec: "DcHoleFeature",
    PatternSpec: "DcRectangularPattern",
    CircularSpec: "DcCircularPattern",
    MirrorSpec: "DcMirrorPattern",
    PlaneSpec: "DcWorkPlane",
    FilletSpec: "DcFilletEdgeFeature",
    ChamferSpec: "DcChamferFeature",
}


def FamilySpec(Features: tuple[KPartFeature, ...]) -> DocumentSpec:
    return DocumentSpec(
        Title="Kit family",
        ParamName="height",
        LengthMm=20.0,
        ProfileKind="part",
        BodyName="Body1",
        Features=Features,
    )
