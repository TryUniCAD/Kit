from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
from subprocess import run
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from NestedRequest import authored_document
from NestedWriteAudit import require
from ReadNestedEvidence import TERMINALS, measured_request
from convert import open_document


def index_graph(assembly):
    names = {row.id: (row.kind, row.name) for row in assembly.definitions}
    instances = sorted(
        (names[row.owner_definition_id], row.order, row.name, names[row.definition_id])
        for row in assembly.instances
    )
    return sorted(names.values()), instances


def measure(workspace):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    rows = []
    for case in TERMINALS:
        request, receipt = measured_request(workspace, case)
        document, output = authored_document(request)
        locator = PureWindowsPath(output["path_name"])
        with TemporaryDirectory(prefix="KitNestedCli.") as folder:
            lane = Path(folder)
            source = lane / "Neutral.json"
            evidence = lane / "Measurement.json"
            source.write_text(document.to_json(), encoding="utf-8")
            evidence.write_text(json.dumps(receipt), encoding="utf-8")
            target = lane / locator.name
            args = [
                sys.executable,
                "-B",
                "-m",
                "convert",
                "convert",
                str(source),
                str(target),
                "--json",
                "--native-measurement",
                str(evidence),
                "--native-destination",
            ]
            wanted = {source, evidence}
            foreign = locator.parent / "Other" / locator.name
            wrong = run(
                [*args, str(foreign)],
                cwd=lane,
                env=env,
                capture_output=True,
                text=True,
                timeout=90,
            )
            require(
                wrong.returncode == 1
                and not wrong.stdout
                and set(lane.iterdir()) == wanted
                and "namespace" in json.loads(wrong.stderr)["message"],
                "different native locator did not refuse before publication: "
                + case
                + " "
                + wrong.stderr[-1200:],
            )
            written = run(
                [*args, str(locator)],
                cwd=lane,
                env=env,
                capture_output=True,
                text=True,
                timeout=90,
            )
            require(written.returncode == 0 and not written.stderr, written.stderr)
            result = json.loads(written.stdout)
            actual = {
                path.name: sha256(path.read_bytes()).hexdigest()
                for path in set(lane.iterdir()) - wanted
            }
            expected = {
                row["name"]: row["sha256"] for row in receipt["receipt"]["members"]
            }
            require(
                actual == expected
                and result["application_usable"] is result["vendor_loadable"] is True
                and not result["dropped"],
                "the CLI did not publish the exact measured bundle",
            )
            reopened = open_document(
                target, strict=True, include_brep=False, include_tessellation=False
            )
            require(
                reopened.assembly is not None
                and index_graph(reopened.assembly) == index_graph(document.assembly),
                "the reopened assembly lost an owned definition name or placement order: "
                + case,
            )
            rows.append(
                {
                    "case": case,
                    "files": actual,
                    "native_flags": True,
                    "wrong_locator_preserved": True,
                    "strict_names_and_local_order": True,
                }
            )
    return {"schema": "kit.sw2026.measured-nested-cli.v1", "cases": rows}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    result = measure(options.workspace)
    raw = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    with options.output.open("xb") as file:
        file.write(raw)
    print(sha256(raw).hexdigest())
