from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Frozen.MatchImports import MatchImports
from tests.Convert.Solidworks.Research.Frozen.RunPinned import RunPinned
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# previous tree acceptance belongs to the exact emitted bytes and immutable producer
def CheckTreeOutput(
    Output: dict[str, object], SourceRoot: FilePath, Revision: object
) -> None:
    assert Output["frozen_generator_revision"] == Revision
    Request = CastValue(dict[str, object], Output["request"])
    Report = RunPinned(Request, SourceRoot, True)
    MatchImports(Report, SourceRoot)
    RawValue = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    assert len(RawValue) == Output["bytes"]
    assert HashBytes(RawValue).hexdigest() == Output["sha256"]
    assert (
        Report["heldout_native_payloads_read"] is Report["native_acceptance"] is False
    )
    GraphValue = CastValue(dict[str, object], Report["graph"])
    assert GraphValue["unresolved_references"] == 0
    Features = CastValue(list[str], Report["features"])
    assert Features.count("moInkMarkupFolder_c") == 1
    assert "moNotesAreaFtrFolder_c" not in Features and len(Features) == 19
    Report["frozen_generator_revision"] = Revision
    Report["private_reference_observations_read"] = False
    Report["historical_output_identical"] = True
    Report["new_unseen_evidence"] = False
    Report["native_acceptance_inherited"] = False
    SavePartOutput("Tree" + CastValue(str, Output["name"]), Request, Report)
