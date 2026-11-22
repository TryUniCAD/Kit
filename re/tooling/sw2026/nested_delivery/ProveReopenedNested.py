from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from os import getpid
from pathlib import Path, PureWindowsPath
from subprocess import run
from tempfile import TemporaryDirectory
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks import SldprtAdapter
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepNestedPlan import PrepNestedPlan
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.ColdNestedPlan import ColdNestedPlan
from interchange.assembly.MateGroup import MateGroup
from interchange.document.Behavior.DocumentIo import ToJson
from NestedRequest import checked, require
from NestedWriteAudit import Audit, snapshot
from ProveMeasuredNested import run_worker as prove_authored
from ReadNestedEvidence import TERMINALS, measured_request

REFUSALS = {
    "changed_native_label": "SOLIDWORKS nested readback differs from its regenerated bundle",
    "unrepresented_mate_group": "does not support the destination",
    "contradicted_pose": "does not support the destination",
    "receipt_child_order": "does not match the exact member",
    "duplicate_receipt_alias": "duplicate member identities",
}


def edited_label(document):
    assembly = document.assembly
    member = next(row for row in assembly.documents if len(row.document.parameters) == 3)
    part = member.document
    sketch, = part.sketches
    label = sketch.constraints[-1]
    assert label.kind == "distance"
    x, y, z = label.attributes["native_display_text_point_m"]
    changed = replace(label, attributes={**label.attributes, "native_display_text_point_m": (x, y, z + 0.0001)})
    sketch = replace(sketch, constraints=(*sketch.constraints[:-1], changed))
    member_value = replace(member, document=replace(part, sketches=(sketch,)))
    return replace(document, assembly=replace(assembly, documents=tuple(
        member_value if value.id == member.id else value for value in assembly.documents
    )))


def load_bundle(folder, envelope):
    members = envelope["receipt"]["members"]
    for row in members:
        data = checked(folder / row["name"], row["sha256"])
        require(len(data) == row["bytes"], "disclosed member size changed")
    return open_document(folder / members[-1]["name"])


def compare_candidates(document, native_path, epoch, expected):
    plan = ColdNestedPlan(document)
    built = PrepNestedPlan(plan, native_path, epoch)
    hashes = {path.name: {"bytes": len(value.BytesValue), "sha256": sha256(value.BytesValue).hexdigest()}
              for path, value in built}
    require(hashes == expected, "altered presentation unexpectedly changed the candidate construction")


def prepare_contrast(document, envelope, mode, native_path, expected):
    graph = document.assembly
    if mode == "changed_native_label":
        document = edited_label(document)
        compare_candidates(document, native_path, envelope["written_at"], expected)
    elif mode == "unrepresented_mate_group":
        group = MateGroup("group/extra", "Authored unmapped group", graph.root_definition_id, ())
        document = replace(document, assembly=replace(graph, mate_groups=(group,)))
    elif mode == "contradicted_pose":
        row, *tail = graph.instances
        values = list(row.transform.values)
        values[3] += 4.0
        row = replace(row, transform=replace(row.transform, values=tuple(values)))
        document = replace(document, assembly=replace(graph, instances=(row, *tail)))
    elif mode == "receipt_child_order":
        envelope["receipt"]["members"][-1]["children"].reverse()
    elif mode == "duplicate_receipt_alias":
        rows = envelope["receipt"]["members"]
        rows[1]["id"] = rows[0]["id"]
    return document


def worker(job, area):
    mode, route = job["mode"], job["route"]
    envelope = deepcopy(job["envelope"])
    initial_receipt = json.dumps(envelope, sort_keys=True)
    folder = Path(job["folder"])
    document = load_bundle(folder, envelope)
    members = envelope["receipt"]["members"]
    expected = {row["name"]: {key: row[key] for key in ("bytes", "sha256")} for row in members}
    target = area / members[-1]["name"]
    native_path = str(PureWindowsPath(envelope["receipt"]["namespace"]) / target.name)
    document = prepare_contrast(document, envelope, mode, native_path, expected)
    document.assert_valid()
    original = ToJson(document, IndentSize=None)
    opts = {"native_destination": native_path, "allow_carrier": False, "require_native_transfers": True,
            "solidworks_native_measurement": envelope}
    if mode != "measured":
        (area / "Existing.bin").write_bytes(b"caller-owned sentinel remains intact")
    before = snapshot(area)
    capabilities = GetDocumentCaps(document)
    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    audit = Audit(area, target, area / members[-2]["name"], expected, mode)
    sys.addaudithook(audit.inspect)
    result, error = None, None
    try:
        if route == "registry":
            result = write_document(document, target, destination_format="solidworks.sldasm",
                                    configuration=document.configurations[0].id, allow_carrier=False, values=opts)
        else:
            result = SldprtAdapter().write(document, target, WriteOptions(configuration=document.configurations[0].id, values=opts))
    except (ValueError, NotFoundError) as caught:
        error = caught
    finally:
        audit.active = False
    require(ToJson(document, IndentSize=None) == original, "source neutral state was changed")
    require(not audit.attempts and not any(name.startswith(("pythoncom", "win32com", "FreeCAD"))
                                           for name in sys.modules), "writer touched external input or a CAD runtime")
    for row in members:
        checked(folder / row["name"], row["sha256"])
    after = snapshot(area)
    common = {"process": getpid(), "route": route, "mode": mode, "runtime_input_reads": 0}
    if mode != "measured":
        require(error is not None and REFUSALS[mode] in str(error), f"unexpected refusal: {error}")
        require(result is None and not audit.staged_write_attempts and not audit.published
                and before == after, "refusal affected caller-owned output")
        return {**common, "refusal": type(error).__name__, "source_and_destination_unchanged": True,
                "staged_writes": 0, "final_writes": 0}
    require(json.dumps(envelope, sort_keys=True) == initial_receipt, "writer replaced or modified the genuine receipt")
    require(result is not None and error is None and after == expected and result.path == target
            and result.application_usable and result.vendor_loadable and not result.dropped
            and not result.carrier_capabilities and not result.requirements
            and result.native_capabilities == capabilities and set(audit.published) == set(expected),
            f"reopened write did not match measured native output: {error}")
    return {**common, "files": after, "native_transfers": len(result.native_capabilities),
            "application_usable": True, "vendor_loadable": True, "source_and_receipt_unchanged": True}


def launch(job):
    with TemporaryDirectory(prefix="KitReopenedAsm.") as area:
        process = run((sys.executable, "-I", "-B", str(HERE), "--worker", str(Path(area).resolve())),
                      input=json.dumps(job), text=True, capture_output=True, timeout=180)
    require(process.returncode == 0 and not process.stderr, f"{job['mode']} {job['route']}: {process.stderr[-4500:]}")
    return json.loads(process.stdout)


def prove(workspace):
    passes, refusals = {}, []
    for case in TERMINALS:
        request, envelope = measured_request(workspace, case)
        folder = workspace / case / "FrozenGenerated"
        request_value = {"folder": str(folder), "envelope": envelope}
        pairs = []
        for route in ("registry", "adapter"):
            observed = launch({**request_value, "route": route, "mode": "measured"})
            authored = prove_authored(request, envelope, route, "measured")
            require(observed["files"] == authored["files"], "existing authored route changed its measured archive identities")
            pairs.append(observed)
            if case == "SdkRepeatedDimensionedNative01":
                for mode in REFUSALS:
                    refusals.append(launch({**request_value, "route": route, "mode": mode}))
        passes[case] = pairs
    processes = [row["process"] for runs in passes.values() for row in runs] + [row["process"] for row in refusals]
    require(len(set(processes)) == len(processes), "guarded processes were reused")
    return {"schema": "kit.sw2026.reopened-nested-exact.v1", "passed": True,
            "native_processes_started": 0, "protected_inputs_read": 0,
            "guarded_publication_workers": len(processes), "authored_regression_workers": 8,
            "reopened_bundles": passes, "refusals": refusals}


def main():
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker is not None:
        print(json.dumps(worker(json.load(sys.stdin), args.worker), sort_keys=True, allow_nan=False))
    else:
        body = (json.dumps(prove(args.workspace), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as output:
            output.write(body)
        print(sha256(body).hexdigest())


if __name__ == "__main__":
    main()
