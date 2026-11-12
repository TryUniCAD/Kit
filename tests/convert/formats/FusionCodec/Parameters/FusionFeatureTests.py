from pathlib import Path as FilePath

from pytest import mark as TestMarks

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.Fusion.Adapter import FusionReader
from tests.convert.formats.FusionCodec.Parameters.RebuildParams import RebuildParams

KFeatureRoot = (
    FilePath(__file__).resolve().parents[5] / "re/Fusion/LocalOracle/Features"
)


@TestMarks.parametrize(
    "FileName",
    ("circle_sketch.f3d", "extrude_07mm.f3d", "extrude_13mm.f3d"),
)
def TestFeatureArchives(FileName: str) -> None:
    Source = KFeatureRoot / FileName
    Rebuilt = RebuildParams(Source)
    Reader = FusionReader()
    Options = ReadOptions(strict=False)
    Before = Reader.Read(Source, Options)
    After = Reader.Read(Rebuilt, Options)
    assert Before.parameters == After.parameters
    assert Before.feature_timeline == After.feature_timeline
    assert Before.diagnostics == After.diagnostics
