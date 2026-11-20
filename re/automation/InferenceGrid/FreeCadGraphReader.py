# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from copy import deepcopy
import difflib
import hashlib
import json
import os
from pathlib import Path
from runpy import run_path
import subprocess
import sys


def probe_remaining(graph, changes, bindings):
    from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
    from convert.adapters.freecad.InlineRead.ReadInline import ReadExpected, ReadInlineDepth, ReadInlineExpr

    candidate = deepcopy(graph["candidate"])
    for key in {row["kit_feature_id"] for row in changes}:
        baseline = RequireEditObj(ReadExpected(candidate), key, "Part::Extrusion")
        step, = (s for s in candidate["feature_timeline"]["$tuple"] if s["id"] == key)
        for field in ReadInlineExpr(baseline).keys() - bindings.keys():
            before = ReadInlineDepth(baseline, field)
            after = before + max(1.0, abs(before) / 4)
            matches = []
            for parameter in candidate["parameters"]["$tuple"]:
                value = parameter["value"]
                if (parameter["owner_id"] != key or parameter["id"] not in step["parameter_ids"]["$tuple"]
                        or parameter["role"]["value"] != "driving" or parameter["expression"]
                        or value["unit"] != "mm" or value["value"] != before):
                    continue
                for slot, item in step["definition"].items():
                    if not isinstance(item, dict) or item != value:
                        continue
                    value["value"] = item["value"] = after
                    try:
                        emitted = RequireEditObj(ReadExpected(candidate), key, "Part::Extrusion")
                        if all(ReadInlineDepth(emitted, name) == (after if name == field else ReadInlineDepth(baseline, name))
                               for name in ("LengthFwd", "LengthRev")):
                            matches.append(slot)
                    except ValueError:
                        continue
                    finally:
                        value["value"] = item["value"] = before
            if len(matches) == 1:
                bindings[field] = matches[0]


def graph_reader(root, scratch, source, pin, changes, graph):
    bindings = {}
    for edit, update in zip(changes, graph["updates"], strict=True):
        if bindings.setdefault(edit["field"], update["definition_field"]) != update["definition_field"]:
            return None
    observed = dict(bindings)
    probe_remaining(graph, changes, bindings)
    path = "re/FreeCad/DerivedReaders/" + "_".join(sorted(bindings)) + "Reader.py"
    if (root / path).exists():
        return None
    code = (Path(__file__).read_text().split("from copy import deepcopy", 1)[0] + '''import json
from pathlib import Path
import sys

from InferenceGrid.FreeCadDepthEdits import depth_edits, reconcile_depths
from InferenceInputs import read_file


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("supply one native FreeCAD part")
    try:
        data = read_file(Path(sys.argv[1]), 128 * 1024 * 1024)
        result = reconcile_depths(data, depth_edits(data), ''' + repr(dict(sorted(bindings.items()))) + ''')
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
    if result["status"] != "candidate_matches_native_graph":
        raise SystemExit(2)
    print(json.dumps(result))
''')
    script = scratch / "EditedDepthReader.py"
    script.write_text(code)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": os.pathsep.join(
        map(str, (root / "src", root / "re/automation")))}
    run = subprocess.run([sys.executable, script, source], cwd=scratch, env=env,
                         capture_output=True, timeout=90)
    if run.returncode or json.loads(run.stdout) != graph:
        return None
    from InferenceGrid.FreeCadDepthEdits import depth_edits, reconcile_depths
    from InferenceInputs import read_file

    verified = set()
    replays = []
    folder = root / "re/FreeCad/Verification"
    for case in run_path(str(folder / "Cases.py"))["KCases"].values():
        if case["mode"] != "refused" or case["sha256"] == pin or Path(case["file"]).name != case["file"]:
            continue
        data = read_file(folder / case["file"], 16 * 1024 * 1024)
        if hashlib.sha256(data).hexdigest() != case["sha256"]:
            return None
        native_changes = depth_edits(data)
        if not native_changes or any(change["field"] not in bindings for change in native_changes):
            continue
        comparison = reconcile_depths(data, native_changes)
        if comparison["status"] != "candidate_matches_native_graph":
            return None
        control = scratch / "graph-control.FCStd"
        control.write_bytes(data)
        replay = subprocess.run([sys.executable, script, control], cwd=scratch, env=env,
                                capture_output=True, timeout=90)
        if replay.returncode:
            return None
        record = json.loads(replay.stdout)
        if record != comparison:
            return None
        slots = sorted({u["definition_field"] for u in record["updates"]})
        verified.update(slots)
        replays.append({"control_sha256": case["sha256"], "definition_fields": slots})
    if not set(bindings.values()) <= verified:
        return None
    return {"path": path, "patch": "".join(difflib.unified_diff([], code.splitlines(True), "/dev/null", "b/" + path)),
            "base": subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip(),
            "input_sha256": pin, "reader_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "bindings": bindings, "observed_bindings": observed, "control_replays": replays,
            "verification": "input_and_independent_saved_edits"}
