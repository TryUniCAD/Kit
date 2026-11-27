from hashlib import sha256 as HashBytes

from pytest import mark as MarkTests

from convert.adapters.Fusion.Native.Circular.RimFillet.CenterRimTensor import (
    CenterRimTensor,
)
from convert.adapters.Fusion.Native.Circular.RotaryMass import CacheNumbers
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    ObjectFields,
    PointCoords,
    NumberValue,
)
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Geometry.Extrude.Circular.DualSide.BuildDualSide import BuildDualSide
from convert.Geometry.Extrude.Circular.DualSide.MeasureDualMass import MeasureDualMass
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# independent translated native controls distinguish origin tensors from centroidal tensors in both planes
@MarkTests.parametrize(
    "Sample",
    tuple(
        Value
        for Value in ReadDualCases()
        if Value.Identity
        in (
            "baseline",
            "baseline_edit_first",
            "frame",
            "frame_edit_second",
            "holdout_a",
            "holdout_b",
        )
    ),
)
def CheckTensorRead(Sample: DualCase) -> None:
    Encoded = Sample.Source.read_bytes()
    assert HashBytes(Encoded).hexdigest() == Sample.Digest
    Model = ReadDocument(Encoded)
    Cache = ObjectFields(BuildGraph(Model).OneClass("Body").Fields["cache"])
    _, Volume, AreaValue, Center, _ = BuildDualSide(
        Sample.Identity,
        Sample.Frame,
        Sample.Profile,
        Sample.FirstMm,
        Sample.SecondMm,
        Sample.FirstTaper,
        Sample.SecondTaper,
    )
    Diagonal, CrossTerms = MeasureDualMass(
        Sample.Frame,
        Sample.Profile,
        Sample.FirstMm,
        Sample.SecondMm,
        Sample.FirstTaper,
        Sample.SecondTaper,
    )
    ExpectedCenter = (Center.x / 10, Center.y / 10, Center.z / 10)
    ExpectedDiagonal = (Diagonal.x / 100000, Diagonal.y / 100000, Diagonal.z / 100000)
    ExpectedCross = (
        CrossTerms.x / 100000,
        CrossTerms.y / 100000,
        CrossTerms.z / 100000,
    )
    CacheNumbers(
        (NumberValue(Cache["volume"]), NumberValue(Cache["area"])),
        (Volume / 1000, AreaValue / 100),
    )
    CacheNumbers(PointCoords(Cache["cog"]), ExpectedCenter)
    CacheNumbers(PointCoords(Cache["moi"]), ExpectedDiagonal)
    Actual = CenterRimTensor(
        NumberValue(Cache["volume"]),
        PointCoords(Cache["cog"]),
        PointCoords(Cache["moi"]),
        PointCoords(Cache["moiOffDiag"]),
    )
    Expected = CenterRimTensor(
        Volume / 1000, ExpectedCenter, ExpectedDiagonal, ExpectedCross
    )
    CacheNumbers(Actual[0], Expected[0])
    CacheNumbers(Actual[1], Expected[1])
