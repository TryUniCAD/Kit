# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from datetime import datetime, timedelta, timezone
import re
from hashlib import sha256
import json
from math import isclose, isfinite
from pathlib import Path
import sys

if not __debug__:
    raise RuntimeError("Run verification without Python optimization")

root = Path(sys.argv[1]).resolve()
revision = sys.argv[2]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((root / name).read_bytes())


def near(actual, expected):
    assert isinstance(actual, (int, float)) and not isinstance(actual, bool)
    assert isfinite(actual)
    return isclose(actual, expected, rel_tol=0.0, abs_tol=1e-8)


def session(run, expected_phase):
    assert run["phase"] == expected_phase
    assert type(run["pid"]) is int and 0 < run["pid"] < 2**32
    assert re.fullmatch(r"windows:[1-9][0-9]{0,19}", run["process_start"])
    ticks = int(run["process_start"].split(":", 1)[1])
    assert ticks < 2**64
    birth = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(
        microseconds=ticks // 10
    )
    started = datetime.fromisoformat(run["started_utc"])
    ended = datetime.fromisoformat(run["ended_utc"])
    assert started.utcoffset() == ended.utcoffset() == timedelta(0)
    assert birth <= started < ended
    assert started - birth < timedelta(minutes=5)
    return birth


def shape(value, lo, hi):
    assert value["shape_type"] == "Solid" and value["is_valid"]
    assert value["body_count"] == 1
    assert near(value["volume_mm3"], 37 * 21 * (hi - lo))
    bounds = value["world_bounds_mm"]
    assert len(bounds) == 2 and all(len(vector) == 3 for vector in bounds)
    assert len(value["com_mm"]) == 3
    assert all(
        near(actual, expected)
        for vector, target in zip(bounds, ((0, 0, lo), (37, 21, hi)), strict=True)
        for actual, expected in zip(vector, target, strict=True)
    )
    assert all(
        near(actual, expected)
        for actual, expected in zip(
            value["com_mm"], (18.5, 10.5, (lo + hi) / 2), strict=True
        )
    )


preparation = load("Preparation.json")
edited = load("SavedAlias-edit.json")
reopened = load("SavedAlias-reopen.json")
baseline = load("Native-edit.json")
assert (
    preparation["revision"]
    == edited["source_revision"]
    == reopened["source_revision"]
    == revision
)
assert (
    digest(root / "Preparation.json")
    == edited["preparation_sha256"]
    == reopened["preparation_sha256"]
)
assert edited["pid"] != reopened["pid"]
assert edited["process_start"] != reopened["process_start"]
assert edited["session"] != reopened["session"]
assert session(edited, "edit") < session(reopened, "reopen")
assert datetime.fromisoformat(edited["ended_utc"]) < datetime.fromisoformat(
    reopened["started_utc"]
)
assert edited["collector_sha256"] == reopened["collector_sha256"]
assert any(
    path.is_file() and digest(path) == edited["collector_sha256"]
    for path in (
        root / "SavedAliasWitness.py",
        Path(__file__).with_name("CollectSavedAliases.py"),
    )
)
for run in (edited, reopened):
    assert datetime.fromisoformat(run["started_utc"]) < datetime.fromisoformat(
        run["ended_utc"]
    )
    assert not run["documents_after_close"]
    assert run["native_version"] == baseline["native_version"]
    assert run["native_modules"] == baseline["native_modules"]
    for module in run["native_modules"].values():
        assert digest(Path(module["path"])) == module["sha256"]
    for control in ("before", "after"):
        assert run["controls"][control]["native_type"] == "Part::Box"
        assert run["controls"][control]["recomputed"] > 0
        shape(run["controls"][control], -5, 11)

expected = {
    "forward-depth_forward": (14, 5, -5, 14),
    "forward-depth_reverse": (11, 8, -8, 11),
    "reversed-depth_forward": (14, 5, -14, 5),
    "reversed-depth_reverse": (11, 8, -11, 8),
    "symmetric-depth_total": (20, 0, -10, 10),
    "alias_mixed": (11, 5, -5, 11),
    "alias_equal_reordered": (7, 7, -7, 7),
    "alias_edited": (14, 5, -5, 14),
}
assert set(edited["cases"]) == set(reopened["cases"]) == set(expected)
cases = {}
for name, (forward, reverse, lo, hi) in expected.items():
    left = edited["cases"][name]
    right = reopened["cases"][name]
    path = (root / left["path"]).resolve()
    assert path.is_relative_to(root)
    assert digest(path) == left["sha256"] == right["sha256"]
    assert left["recompute"] > 0
    for state in (left["edited"], right["loaded"], right["rebuilt"]):
        feature = state["feature"]
        assert feature["native_type"] == "Part::Extrusion"
        assert feature["linked_sketch"]["type"] == "Sketcher::SketchObject"
        assert feature["linked_sketch"]["geometry_count"] == 4
        assert feature["solid"] and feature["dir"] == [0.0, 0.0, 1.0]
        assert feature["reversed"] == name.startswith("reversed-")
        assert feature["symmetric"] == name.startswith("symmetric-")
        assert feature["state"] == ["Up-to-date"]
        assert near(feature["length_fwd_mm"], forward)
        assert near(feature["length_rev_mm"], reverse)
        assert feature["expressions"] == left["edited"]["feature"]["expressions"]
        assert state["spreadsheet"] == left["edited"]["spreadsheet"]
        shape(feature["geometry"], lo, hi)
    if left["kind"] == "inline_saved_edit":
        assert left["original_unchanged"]
        assert left["before"] == left["restored_unsaved"]
        source_name = name.split("-", 1)[0]
        package = preparation["packages"][source_name]
        assert (
            digest(root / "Originals" / package["path"])
            == package["sha256"]
            == left["source_sha256"]
        )
    else:
        assert left["kind"] == "native_only_alias"
        assert left["edited"]["feature"]["expressions"] == {
            "LengthFwd": "DepthInputs.FrontCap",
            "LengthRev": "DepthInputs.RearCap",
        }
    cases[name] = {
        "path": left["path"],
        "sha256": left["sha256"],
        "kind": left["kind"],
        "geometry": right["loaded"]["feature"]["geometry"],
        "expressions": right["loaded"]["feature"]["expressions"],
        "spreadsheet": right["loaded"]["spreadsheet"],
    }
report = {
    "source_revision": revision,
    "preparation_sha256": digest(root / "Preparation.json"),
    "edit_receipt_sha256": digest(root / "SavedAlias-edit.json"),
    "reopen_receipt_sha256": digest(root / "SavedAlias-reopen.json"),
    "collector_sha256": edited["collector_sha256"],
    "verifier_sha256": digest(Path(__file__)),
    "controls_healthy": True,
    "fresh_reopen": True,
    "result": "observed_saved_edit_and_alias_reopen",
    "qualification": "not_evaluated",
    "cases": cases,
}
destination = (
    root / (sys.argv[3] if len(sys.argv) > 3 else "VerifiedSavedAliases.json")
).resolve()
assert destination.is_relative_to(root)
if destination.exists():
    raise FileExistsError(destination)
destination.write_text(
    json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
    encoding="utf-8",
)
print(
    json.dumps(
        {
            "result": report["result"],
            "cases": len(cases),
            "report_sha256": digest(destination),
        },
        sort_keys=True,
    )
)
