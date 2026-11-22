from json import loads as LoadJson

from tests.Convert.Solidworks.Configuration.MaterialVisual.RunVisualCase import (
    RunVisualCase,
)


# the existing native boss needs its physical name and visual owners in the inherited map
def TestPartVisual() -> None:
    Outcome = RunVisualCase(
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
    )
    assert Outcome.returncode == 0 and not Outcome.stderr, Outcome.stderr
    ReportValue = LoadJson(Outcome.stdout)
    assert ReportValue["prefix_span"] == [18, 925]
    assert ReportValue["visual_span"] == ["moVisualProperties_c", 7, 82, 925]
    assert ReportValue["prefix_map"] == {"entry_counter": 4, "end_counter": 8}
    assert ReportValue["identity"] == "Steel"
    assert ReportValue["selector"] == [1, 0, 1, 0, 1]
    assert ReportValue["texture_calls"] == 0
    assert ReportValue["exact_typed_replay"] is True
    assert ReportValue["runtime_input_or_process_accesses"] == 0


# an independently saved import keeps its other visual mode outside the bounded reader
def TestOtherVisual() -> None:
    Outcome = RunVisualCase(
        "local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
    )
    assert Outcome.returncode != 0 and not Outcome.stdout
    assert Outcome.stderr.rstrip().endswith(
        b"BodyUnsupported: unsupported SOLIDWORKS part material visual selectors"
    ), Outcome.stderr
