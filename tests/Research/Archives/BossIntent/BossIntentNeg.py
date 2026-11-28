from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.BossIntent.ChangeBossRules import ChangeRules
from tests.Research.Archives.BossIntent.RunBossIntent import RunIntentStep
from tests.Research.Archives.BossIntent.ShiftBossOwner import ShiftOwnerSpan


# the logical proof must reject wrong edges reversed operands and false source custody without creating output
def VerifyRefusals(
    TmpPath: FilePath,
    SourceBytes: bytes,
    OutputPath: FilePath,
) -> None:
    Changed = TmpPath / "Changed.json"
    Refused = TmpPath / "Refused.json"
    InputDoc = CadDocument.from_json(SourceBytes.decode("utf-8"))
    Cases = [
        (CaseDoc, "P03 ordered constraint endpoints differ")
        for CaseDoc in ChangeRules(InputDoc)
    ]
    Cases.append((ShiftOwnerSpan(InputDoc), "P03 sketch owner span differs"))
    Cases.append(
        (
            ReplaceValue(
                InputDoc, metadata={**InputDoc.metadata, "audit_label": "changed"}
            ),
            "P03 source JSON differs from the exact pinned strict read",
        )
    )
    for CaseDoc, Message in Cases:
        _ = Changed.write_text(CaseDoc.to_json(), encoding="utf-8")
        Result = RunIntentStep(
            TmpPath, "prepare", "--input", str(Changed), "--output", str(Refused)
        )
        assert Result.returncode == 1 and Message in Result.stderr
        assert not Refused.exists()
    Retained = TmpPath / "RetainedSource.json"
    assert Retained.read_bytes() == SourceBytes
    for Existing in (Retained, OutputPath):
        Before = Existing.read_bytes()
        Result = RunIntentStep(
            TmpPath, "prepare", "--input", str(Retained), "--output", str(Existing)
        )
        assert Result.returncode == 1 and "P03 output already exists" in Result.stderr
        assert Existing.read_bytes() == Before
