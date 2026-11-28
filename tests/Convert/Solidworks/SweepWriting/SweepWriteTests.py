from json import loads as ReadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue


# the normal stream registry and direct writer must reproduce the measured sweep lifecycle in fresh processes
def TestSweepWrite() -> None:
    Repository = FilePath(__file__).resolve().parents[4]
    ScriptValue = Repository / "re/tooling/sw2026/CheckScopedSweep.py"
    ProcessValue = RunProcess(
        (PythonExe, "-I", "-B", str(ScriptValue)),
        cwd=Repository,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert ProcessValue.returncode == 0, ProcessValue.stderr
    ReportValue = CastValue(dict[str, object], ReadJson(ProcessValue.stdout))
    assert ReportValue["writer_processes"] == 2
    assert ReportValue["native_calls"] == 0
    for CaseValue in CastValue(list[dict[str, object]], ReportValue["cases"]):
        assert CaseValue["exact_registry_and_direct_streams"] is True
        assert CaseValue["native_transfers"] == 6
        assert CaseValue["normalized_state_checks"] == 30
        assert CaseValue["writer_runtime_input_reads"] == 0
        assert CaseValue["occupied_stream_and_unverified_path_refused"] is True
        assert {
            "swapped_controls",
            "swapped_edit_reopen",
            "unmeasured_model",
            "unmeasured_path_edit",
            "shifted_locator",
            "shifted_epoch",
        } <= set(CastValue(list[str], CaseValue["fresh_attempt_refusals"]))
        ReadbackValue = CastValue(dict[str, object], CaseValue["sdk_readback"])
        assert (ReadbackValue["config_map"], ReadbackValue["resolved_map"]) == (
            101,
            225,
        )
        assert ReadbackValue["typed_stream_replays"] == 2
        assert ReadbackValue["density_object_span"] == ["Contents/Config-0", 2068, 2127]
        VerifySwScopes(ReadbackValue)
        assert len(CastValue(list[str], ReadbackValue["rejected_sources"])) == 3
        ModesValue = CastValue(
            list[dict[str, object]], ReadbackValue["strict_readback"]
        )
        assert [
            (ModeValue["include_brep"], ModeValue["native_transfers"])
            for ModeValue in ModesValue
        ] == [(True, 8), (False, 7)]
        assert all(
            ModeValue["strict_reader_routes"]
            == ModeValue["permissive_typed_routes"]
            == ModeValue["exact_republication_routes"]
            == 2
            for ModeValue in ModesValue
        )


# the ordinary reader and neutral writer must verify actual linked configuration and sketch content
def VerifySwScopes(ReadbackValue: dict[str, object]) -> None:
    assert ReadbackValue["portable_cli"] == {
        "neutral_round_trip": True,
        "whole_semantic_document_equal": True,
        "incomplete_sweep_geometry_refusals": 3,
    }
    SavedEnvelope = CastValue(dict[str, object], ReadbackValue["saved_envelope"])
    assert SavedEnvelope["strict_refusals"] == 8
    assert SavedEnvelope["legacy_permissive_routes"] == 2
    assert SavedEnvelope["selected_configuration_checks"] == 24
    assert SavedEnvelope["multi_config_saved_refusals"] == 8
    assert SavedEnvelope["unrelated_physical_lane_reads"] == 8
    assert SavedEnvelope["explicit_reads_independent_of_default_lane"] == 4
