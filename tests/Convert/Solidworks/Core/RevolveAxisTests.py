from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as Interpreter
from typing import cast as CastValue
from interchange import RevolutionFeature
from convert.adapters.solidworks.Core.Adapter import (
    NativePartModel,
    ReadSldprt,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive

# the sample cases must remain explicit so format translation exercises the intended compatibility boundary
KSample = (
    FilePath(__file__).parents[4]
    / "re"
    / "solidworks"
    / "examples"
    / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
    / "10MM x 20MM x 13MM head 316 Stainless Steel Socket Head Screw.SLDPRT"
)


# the axis owner contract needs boundary coverage so independent codecs retain consistent data contracts
def TestAxisOwner() -> None:
    Archive = SldprtArchive.open(KSample)
    Model = NativePartModel(Archive, None)
    Operation = next(
        ItemValue for ItemValue in Model.operations if ItemValue.object_id == 144
    )
    assert Operation.profile_id == 130
    assert Operation.axis_source_id == 63
    assert 63 in Operation.dependencies
    Document = ReadSldprt(KSample, include_brep=False)
    Feature = next(
        ItemValue
        for ItemValue in Document.feature_timeline
        if ItemValue.name == "Revolve1"
    )
    assert "sldprt:feature:63" in Feature.input_feature_ids
    assert Feature.sketch_id == "sldprt:sketch:130"
    Definition = Feature.definition
    assert isinstance(Definition, RevolutionFeature)
    if Operation.axis_marker_offset is None:
        assert Definition.axis_entity_id == "sldprt:sketch:63"
    else:
        AxisSketch = next(
            ItemValue
            for ItemValue in Document.sketches
            if ItemValue.id == "sldprt:sketch:63"
        )
        assert Definition.axis_entity_id in {
            ItemValue.id for ItemValue in AxisSketch.entities
        }
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = RootValue / "re/tooling/sw2026/revolve/CheckPrincipalQueueCase.py"
    for CaseValue in ("Top", "Right"):
        Result = RunProcess(
            [Interpreter, "-I", "-B", str(Worker), "--case", CaseValue],
            cwd=RootValue,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert Result.returncode == 0, Result.stderr
        ReportValue = CastValue(dict[str, object], LoadJson(Result.stdout))
        assert ReportValue["exact_native_hash"] is True
        assert ReportValue["publications"] == 4
