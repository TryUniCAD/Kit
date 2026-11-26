# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import json
import subprocess
import sys

if not __debug__:
    raise RuntimeError("Run verification without Python optimization")

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()
revision = sys.argv[3]
root.mkdir(parents=True, exist_ok=False)
research = repo / "re/automation"
sys.path.insert(0, str(research))
from FreeCadTwoLengthReadiness import BuildCase, ObserveNative, ReadinessCase
from convert.api.ApiWrite import WriteDocument
from convert.adapters.registry import ApplicationUsabilityError
from interchange.document.Models.DocumentModel import CadDocument


def git(*args):
    return (
        subprocess.check_output(["rtk", "proxy", "git", *args], cwd=repo, timeout=30)
        .decode()
        .strip()
    )


assert git("rev-parse", "HEAD") == revision and not git(
    "status", "--porcelain=v1", "--untracked-files=all"
)
files = root / "Originals"
files.mkdir(exist_ok=True)
assert not list(files.iterdir())
rows = {}
for case, reversed_ in (
    (ReadinessCase("forward", 11.0, 5.0), False),
    (ReadinessCase("reversed", 11.0, 5.0), True),
    (ReadinessCase("symmetric", 16.0, None), False),
):
    doc = BuildCase(case)
    if reversed_:
        (feature,) = doc.feature_timeline
        doc = replace(
            doc,
            feature_timeline=(
                replace(feature, definition=replace(feature.definition, reversed=True)),
            ),
        )
    portable = doc.to_json(indent=None).encode("utf-8")
    original_doc = CadDocument.from_json(portable.decode("utf-8"))
    stream = BytesIO()
    try:
        WriteDocument(
            original_doc, stream, DestFormat="freecad.fcstd", AllowCarrier=False
        )
    except ApplicationUsabilityError as error:
        strict_refusal = str(error)
        assert not stream.getvalue()
    else:
        raise ValueError("Strict output admitted an unattested generated file")
    result = WriteDocument(
        original_doc, stream, DestFormat="freecad.fcstd", AllowCarrier=True
    )
    assert result.application_usable is False and result.vendor_loadable is False
    assert (
        result.metadata["application_usable"] is False
        and result.metadata["vendor_loadable"] is False
    )
    native = stream.getvalue()
    assert result.bytes_written == len(native) and not result.carrier_capabilities
    offline = ObserveNative(native, case)
    assert not offline["crossed_drivers"] and not offline["missing_drivers"]
    with ZipFile(BytesIO(native)) as archive:
        shape_entries = [
            name
            for name in archive.namelist()
            if name.lower().endswith((".brp", ".brep"))
        ]
        assert any(name.startswith("RectangularBoss.") for name in shape_entries)
        shape_hashes = {
            name: sha256(archive.read(name)).hexdigest() for name in shape_entries
        }
    neutral_path = files / f"{case.Name}.json"
    neutral_path.write_bytes(portable)
    archive = files / f"{case.Name}.FCStd"
    archive.write_bytes(native)
    rows[case.Name] = {
        "name": case.Name,
        "path": archive.name,
        "sha256": sha256(native).hexdigest(),
        "portable_sha256": sha256(portable).hexdigest(),
        "forward_mm": case.Forward,
        "reverse_mm": case.Reverse,
        "reversed": reversed_,
        "sdk_vendor_loadable": result.vendor_loadable,
        "sdk_application_usable": result.application_usable,
        "carrier": False,
        "strict_refusal": strict_refusal,
        "shape_entry_hashes": shape_hashes,
        "metadata_flags": {
            key: result.metadata[key]
            for key in ("application_usable", "vendor_loadable")
        },
        "archive_metadata": offline,
    }
    print(json.dumps(rows[case.Name], sort_keys=True), flush=True)
manifest = {
    "revision": revision,
    "tree": git("rev-parse", "HEAD^{tree}"),
    "sdk_source_hashes": {
        str(path.relative_to(repo))
        .replace("\\", "/"): sha256(path.read_bytes())
        .hexdigest()
        for path in sorted((repo / "src").rglob("*.py"))
    },
    "writer_source_sha256": sha256(
        (repo / "src/convert/adapters/freecad/Archive.py").read_bytes()
    ).hexdigest(),
    "readiness_source_sha256": sha256(
        (research / "FreeCadTwoLengthReadiness.py").read_bytes()
    ).hexdigest(),
    "sdk_python": sys.version,
    "preparer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    "native_collector_sha256": sha256(
        Path(__file__).with_name("CollectRectangles.py").read_bytes()
    ).hexdigest(),
    "packages": rows,
}
(root / "Preparation.json").write_text(
    json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
)
assert not git("status", "--porcelain=v1", "--untracked-files=all")
print(
    json.dumps(
        {
            "preparation_sha256": sha256(
                (root / "Preparation.json").read_bytes()
            ).hexdigest(),
            "revision": revision,
            "tree": manifest["tree"],
        }
    ),
    flush=True,
)
