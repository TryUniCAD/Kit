from __future__ import annotations

from hashlib import sha256 as HashBytes
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.Frozen.FrozenRoot import FrozenRoot
from tests.Convert.Solidworks.Research.Presentation.CheckTreeOutput import (
    CheckTreeOutput,
)
from tests.Convert.Solidworks.Research.Presentation.MatchTreeFiles import MatchTreeFiles
from tests.Convert.Solidworks.Research.Presentation.VerifyTree import ReadTreeFreeze


# historical folder predictions must reproduce the measured bytes from their original source snapshot
def TestTreeHold() -> None:
    Freeze = ReadTreeFreeze()
    ProofPath = (
        KRepoRoot / "re/solidworks/measurements/2026/TreeHeldoutProcessesE727.json"
    )
    assert HashBytes(ProofPath.read_bytes()).hexdigest() == (
        "e42b686c83b56bf50db2cdf111de168a8587e78366cbd437b340e231c0a650b5"
    )
    Receipt = ReadObject(ProofPath)
    assert Receipt["writer_revision"] == Freeze["writer_revision"]
    assert Receipt["private_reference_api_observations_inspected"] is False
    assert Receipt["native_reference_payloads_inspected"] is False
    Outputs = CastValue(list[dict[str, object]], Receipt["outputs"])
    Locked = CastValue(list[dict[str, object]], Freeze["evaluated_heldouts"])
    assert len(Outputs) == len(Locked) == 2
    assert {Value["name"] for Value in Outputs} == {Value["name"] for Value in Locked}
    Inventory = {
        "source_revision": Freeze["writer_revision"],
        "source_tree": Freeze["writer_tree"],
        "source_file_count": Freeze["constructor_dependency_count"],
        "files": Freeze["files"],
    }
    with FrozenRoot(Inventory) as SourceRoot:
        MatchTreeFiles(Freeze, SourceRoot)
        for Output in Outputs:
            CheckTreeOutput(Output, SourceRoot, Freeze["writer_revision"])
        MatchTreeFiles(Freeze, SourceRoot)
    assert ReadTreeFreeze() == Freeze
