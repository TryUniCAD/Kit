# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def graph_reader(root, scratch, source, pin, changes, graph):
    bindings = {}
    for edit, update in zip(changes, graph["updates"], strict=True):
        if bindings.setdefault(edit["field"], update["definition_field"]) != update["definition_field"]:
            return None
    path = "re/FreeCad/DerivedReaders/" + "_".join(sorted(bindings)) + "Reader.py"
    if (root / path).exists():
        return None
    code = (Path(__file__).read_text().split("import difflib", 1)[0] + '''import json
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
    return {"path": path, "patch": "".join(difflib.unified_diff([], code.splitlines(True), "/dev/null", "b/" + path)),
            "base": subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip(),
            "input_sha256": pin, "reader_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "bindings": bindings, "verification": "exact_input_graph_replay"}
