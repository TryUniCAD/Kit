import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys

from convert import open_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Solidworks.PlainWriting.ReversePrep.MakePrepDoc import MakePrepDoc
from tests.Convert.Solidworks.PlainWriting.ReversePrep.ReadPrepCases import ReadPrepCases

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
output.mkdir(exist_ok=False)
rows = []
for case in ReadPrepCases():
    directory = output / case.NameValue
    directory.mkdir()
    neutral = MakePrepDoc(case)
    candidate = PrepareNative(
        neutral, BytesIO(), 1795737600,
        WriteOptions(values={"final_destination": rf"C:\KitReverseResearch\{case.NameValue}.SLDPRT"}),
    )
    source = root / "re/solidworks/DecodedPromotion20261127/Evidence" / (case.NameValue + ".SLDPRT")
    assert source.read_bytes() == candidate.BytesValue
    native_path = directory / (case.NameValue + ".SLDPRT")
    native_path.write_bytes(candidate.BytesValue)
    document = open_document(native_path)
    restored = CadDocument.from_json(document.to_json())
    regenerated = PrepareNative(
        restored, BytesIO(), 1795737600,
        WriteOptions(values={"final_destination": rf"C:\KitReverseResearch\{case.NameValue}.SLDPRT"}),
    )
    assert regenerated.BytesValue == candidate.BytesValue
    (directory / "Neutral.json").write_text(neutral.to_json(), encoding="utf-8")
    (directory / "Decoded.json").write_text(document.to_json(), encoding="utf-8")
    rows.append({"case": case.NameValue, "reversed": case.IsReversed,
                 "sha256": hashlib.sha256(candidate.BytesValue).hexdigest(),
                 "bytes": len(candidate.BytesValue), "cold_json_regeneration_equal": True,
                 "native_acceptance": False})
paths = [
    "src/convert/adapters/solidworks/Archive/Construction/Blind/BlindEndInput.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/FinishBlindMut.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/Neutral/BlindPlan.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/Neutral/ProjectBlind.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/Neutral/RequireBossDef.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/ReadExtrude.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/ColdPrism.py",
]
paths += [str(path.relative_to(root)) for path in sorted((root / "tests/Convert/Solidworks/PlainWriting/ReversePrep").glob("*.py"))]
bindings = [{"path": name, "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest(), "bytes": (root / name).stat().st_size} for name in paths]
report = {
    "task": "A12-ReverseBlindBoss20261127",
    "base_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
    "binding": "exact working-source hashes; subsequent committed-file replay binds accepted checkpoint",
    "models": False, "native_calls": 0, "native_acceptance": False,
    "sources": bindings, "cases": rows,
    "verification": {"runtime": "CPython 3.14.6; pytest 9.1.1", "integration_passed": 59,
                     "command": "python -m pytest tests/Convert/Solidworks/PlainWriting tests/Convert/Integration/Solidworks/Reverse -q --tb=short",
                     "duration_seconds": 29.88,
                     "independent_review": "no actionable production defect; complete direction flow and unchanged exact publication gate independently inspected"},
    "retained_attempts": [
        {"failure": "six initial test assertions expected topology.valid true", "resolution": "preserved existing unknown native validity None; verified complete solid topology and Document.AssertValid instead"},
        {"failure": "three fresh CLI processes imported stale installed SDK with relative PYTHONPATH", "resolution": "absolute checkout source paths bound through scoped environment fixture; native receipt refusal then verified"},
        {"failure": "combined test collection found duplicate ReverseCliTests basenames", "resolution": "renamed preparation test to PrepCliTests; all 59 archive and process cases pass together"},
        {"failure": "optional feature length rejected by Mypy", "resolution": "assert actual recovered length before measurement comparison"}
    ],
    "remaining": ["generated reversed native lifecycle and independent native holdouts unavailable while CAD API down", "source saved cap-field provenance", "separately owned saved ghost-body grammar", "unresolved native source features prevent full cross-format conversion"]
}
(output / "Receipt.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"cases": len(rows), "all_equal": True, "native_acceptance": False}))
