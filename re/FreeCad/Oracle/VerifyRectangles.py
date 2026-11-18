# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
import json
from math import isclose, isfinite
from datetime import datetime, timedelta, timezone
import re
import subprocess
from pathlib import Path
from zipfile import ZipFile
import sys

if not __debug__:
    raise RuntimeError("Run verification without Python optimization")

root = Path(sys.argv[1]).resolve()
revision = sys.argv[2]
repo = Path(sys.argv[3]).resolve()


def load(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def near(actual, expected):
    assert (
        isinstance(actual, (int, float))
        and not isinstance(actual, bool)
        and isfinite(actual)
    )
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
    assert len(value["world_bounds_mm"]) == 2
    assert all(len(vector) == 3 for vector in value["world_bounds_mm"])
    assert len(value["com_mm"]) == 3
    assert (
        value["is_valid"]
        and value["shape_type"] == "Solid"
        and value["body_count"] == 1
    )
    assert near(value["volume_mm3"], 37 * 21 * (hi - lo))
    assert all(
        near(a, b)
        for v1, v2 in zip(
            value["world_bounds_mm"], ((0, 0, lo), (37, 21, hi)), strict=True
        )
        for a, b in zip(v1, v2, strict=True)
    )
    assert all(
        near(a, b)
        for a, b in zip(value["com_mm"], (18.5, 10.5, (lo + hi) / 2), strict=True)
    )


def feature(data, kind, forward, reverse, lo, hi, require_rebuilt=True):
    value = data["feature"]
    assert (
        value["native_type"] == "Part::Extrusion"
        and value["linked_sketch"]["type"] == "Sketcher::SketchObject"
    )
    assert value["linked_sketch"]["geometry_count"] == 4 and value["solid"]
    assert value["dir"] == [0.0, 0.0, 1.0] and value["dir_mode"] == "Custom"
    assert value["reversed"] == (kind == "reversed") and value["symmetric"] == (
        kind == "symmetric"
    )
    expected_expressions = (
        {"LengthFwd": "Parameters.depth_total"}
        if kind == "symmetric"
        else {
            "LengthFwd": "Parameters.depth_forward",
            "LengthRev": "Parameters.depth_reverse",
        }
    )
    assert value["expressions"] == expected_expressions
    assert value["end_condition"] == (
        "mid_plane" if kind == "symmetric" else "two_lengths"
    )
    assert near(value["length_fwd_mm"], forward) and near(
        value["length_rev_mm"], reverse
    )
    if require_rebuilt:
        assert value["state"] == ["Up-to-date"]
    else:
        assert value["state"] in (["Up-to-date"], ["Touched"])
    shape(value["geometry"], lo, hi)
    return value["geometry"]


prep = load(root / "Preparation.json")
assert len(revision) == 40 and all(char in "0123456789abcdef" for char in revision)
for filename, key in (
    ("PrepareCandidates.py", "preparer_sha256"),
    ("NativeWitness.py", "native_collector_sha256"),
):
    fallback = {
        "PrepareCandidates.py": "PrepareRectangles.py",
        "NativeWitness.py": "CollectRectangles.py",
    }[filename]
    candidates = (root / filename, Path(__file__).with_name(fallback))
    assert any(path.is_file() and digest(path) == prep[key] for path in candidates)
archive_source = "src/convert/adapters/freecad/Archive.py"
committed = subprocess.check_output(
    ["rtk", "proxy", "git", "show", f"{revision}:{archive_source}"],
    cwd=repo,
    timeout=30,
)
assert (
    sha256(committed).hexdigest()
    == prep["writer_source_sha256"]
    == digest(repo / archive_source)
)
source_diff = subprocess.check_output(
    ["rtk", "proxy", "git", "diff", revision, "--", "src"], cwd=repo, timeout=30
)
assert not source_diff
source_tree = (
    subprocess.check_output(
        ["rtk", "proxy", "git", "rev-parse", f"{revision}^{{tree}}"],
        cwd=repo,
        timeout=30,
    )
    .decode()
    .strip()
)
assert source_tree == prep["tree"]
for name, expected_hash in prep.get("sdk_source_hashes", {}).items():
    assert digest(repo / name) == expected_hash
edit = load(root / "Native-edit.json")
reopen = load(root / "Native-reopen.json")
assert (
    prep["revision"] == edit["source_revision"] == reopen["source_revision"] == revision
)
assert (
    digest(root / "Preparation.json")
    == edit["preparation_sha256"]
    == reopen["preparation_sha256"]
)
assert (
    edit["pid"] != reopen["pid"]
    and edit["process_start"] != reopen["process_start"]
    and edit["session"] != reopen["session"]
)
assert edit["native_version"] == reopen["native_version"] and edit["native_version"][
    :3
] == ["1", "1", "4"]
assert session(edit, "edit") < session(reopen, "reopen")
assert datetime.fromisoformat(edit["ended_utc"]) < datetime.fromisoformat(
    reopen["started_utc"]
)
for run in (edit, reopen):
    assert datetime.fromisoformat(run["started_utc"]) < datetime.fromisoformat(
        run["ended_utc"]
    )
    assert int(run["process_start"].removeprefix("windows:")) > 0
    assert digest(Path(run["python"]["path"])) == run["python"]["sha256"]
    for native_module in run["native_modules"].values():
        assert digest(Path(native_module["path"])) == native_module["sha256"]
    assert (
        digest(Path(run["native_library"]["path"])) == run["native_library"]["sha256"]
    )
    assert not run["documents_after_close"]
    assert (
        run["native_library"]["sha256"]
        == "efe57703f688cfefe7a6d806e3ea8592ffce516b06874c58597ab7c460780921"
    )
    assert (
        run["native_modules"]["FreeCAD"]["sha256"]
        == "e6d9c7609613c4f8247b8157386ea27adffa102b3e1f8c5b9b0b0e912e0bfde0"
    )
    for control in ("before", "after"):
        assert (
            run["controls"][control]["native_type"] == "Part::Box"
            and run["controls"][control]["recomputed"] > 0
        )
        shape(run["controls"][control], -5, 11)

baseline = {
    "forward": (11, 5, -5, 11),
    "reversed": (11, 5, -11, 5),
    "symmetric": (16, 0, -8, 8),
}
stimuli = {
    "forward": {"depth_forward": (14, 5, -5, 14), "depth_reverse": (11, 8, -8, 11)},
    "reversed": {"depth_forward": (14, 5, -14, 5), "depth_reverse": (11, 8, -11, 8)},
    "symmetric": {"depth_total": (20, 0, -10, 10)},
}
results = {}
initial_open = {}
for name, expected in baseline.items():
    left, right = edit["cases"][name], reopen["cases"][name]
    assert "error" not in left and "error" not in right
    for run in (edit, reopen):
        model = run["controls"][name]
        assert model["recomputed"] > 0 and model["dir"] == [0.0, 0.0, 1.0]
        assert model["native_type"] == "Part::Extrusion" and model["reversed"] == (
            name == "reversed"
        )
        shape(model["geometry"], *expected[2:])
    geometry_before = left["loaded"]["feature"]["geometry"]
    try:
        feature(left["loaded"], name, *expected, require_rebuilt=False)
        initial_open[name] = "valid_solid_before_recompute"
    except (AssertionError, KeyError, TypeError):
        initial_open[name] = "initial_native_geometry_or_state_failed"
    assert left["initial_recompute"] >= 0 and right["initial_recompute"] >= 0
    before_edit = feature(left["rebuilt"], name, *expected)
    reopened_before = feature(right["loaded"], name, *expected)
    reopened_after = feature(right["rebuilt"], name, *expected)
    feature(left["before_save"], name, *expected)
    edits = {}
    for alias, stimulus in stimuli[name].items():
        attempt = left["edits"][alias]
        assert (
            "error" not in attempt
            and attempt["recompute"] > 0
            and attempt["restore_recompute"] > 0
        )
        feature(attempt["before"], name, *expected)
        changed = feature(attempt["edited"], name, *stimulus)
        feature(attempt["restored"], name, *expected)
        baseline_cells = attempt["before"]["spreadsheet"]
        assert baseline_cells == attempt["restored"]["spreadsheet"]
        assert [
            key
            for key in baseline_cells
            if baseline_cells[key] != attempt["edited"]["spreadsheet"][key]
        ] == [alias]
        edits[alias] = {
            "length_fwd_mm": stimulus[0],
            "length_rev_mm": stimulus[1],
            "geometry": changed,
        }
    original = root / "Originals" / prep["packages"][name]["path"]
    assert (
        digest(original.with_suffix(".json"))
        == prep["packages"][name]["portable_sha256"]
    )
    assert prep["packages"][name]["sdk_vendor_loadable"] is False
    assert prep["packages"][name]["sdk_application_usable"] is False
    saved = root / "Restored" / left["saved_name"]
    assert (
        digest(original)
        == prep["packages"][name]["sha256"]
        == left["original_sha256_before"]
        == right["original_sha256_after"]
    )
    assert left["original_bytes_unchanged"] and right["original_bytes_unchanged"]
    assert digest(saved) == left["saved_sha256"] == right["opened_sha256"]
    with ZipFile(original) as original_zip, ZipFile(saved) as saved_zip:
        for entry, expected_hash in prep["packages"][name][
            "shape_entry_hashes"
        ].items():
            assert sha256(original_zip.read(entry)).hexdigest() == expected_hash
        archive = {
            "source_shape_entries": [
                entry
                for entry in original_zip.namelist()
                if entry.casefold().endswith((".brp", ".brep"))
            ],
            "saved_shape_entries": [
                entry
                for entry in saved_zip.namelist()
                if entry.casefold().endswith((".brp", ".brep"))
            ],
        }
    results[name] = {
        "original_sha256": digest(original),
        "restored_sha256": digest(saved),
        "original_load_geometry": geometry_before,
        "original_load_feature_state": left["loaded"]["feature"]["state"],
        "original_rebuilt_geometry": before_edit,
        "restored_reload_geometry": reopened_before,
        "restored_rebuilt_geometry": reopened_after,
        "archive_shape_entries": archive,
        "independent_edits": edits,
        "driver_expressions": left["rebuilt"]["feature"]["expressions"],
    }
report = {
    "scope": "caller-authored private neutral-to-FreeCAD rectangle witness",
    "result": "observed_native_edit_restore_reopen",
    "before_any_recompute": initial_open,
    "C5_geometry_initial_open_passed": all(
        value == "valid_solid_before_recompute" for value in initial_open.values()
    ),
    "collector_sha256": prep["native_collector_sha256"],
    "verifier_sha256": digest(Path(__file__)),
    "source_revision": prep["revision"],
    "source_tree": prep["tree"],
    "freecad_version": edit["native_version"],
    "preparation_sha256": digest(root / "Preparation.json"),
    "native_edit_receipt_sha256": digest(root / "Native-edit.json"),
    "native_reopen_receipt_sha256": digest(root / "Native-reopen.json"),
    "sessions": [
        {
            "phase": item["phase"],
            "pid": item["pid"],
            "process_start": item["process_start"],
            "session": item["session"],
        }
        for item in (edit, reopen)
    ],
    "independent_controls_healthy": True,
    "originals_retained": True,
    "broader_qualification": "not_evaluated",
    "cases": results,
}
out = (
    root / (sys.argv[4] if len(sys.argv) > 4 else "VerifiedRectangles.json")
).resolve()
assert out.is_relative_to(root)
if out.exists():
    raise FileExistsError(out)
out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(
    json.dumps(
        {
            "result": report["result"],
            "initial_open": report["before_any_recompute"],
            "C5_geometry_initial_open_passed": report[
                "C5_geometry_initial_open_passed"
            ],
            "report_sha256": digest(out),
            "manifest_sha256": report["preparation_sha256"],
            "receipts": [
                report["native_edit_receipt_sha256"],
                report["native_reopen_receipt_sha256"],
            ],
            "cases": {
                name: {
                    key: row[key]
                    for key in (
                        "original_sha256",
                        "restored_sha256",
                        "archive_shape_entries",
                    )
                }
                for name, row in results.items()
            },
        },
        sort_keys=True,
    )
)
