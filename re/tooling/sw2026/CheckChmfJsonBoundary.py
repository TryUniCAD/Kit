from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from subprocess import run
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from CheckMeasuredChamfer import FORMAT, OPTION, build_request, check_public, demand, digest
from CheckScopedPlainWriter import WriterAudit, reject

JSON = "interchange.json"
SNAPSHOT = "solidworks_cold_chamfer_source"
SOURCE = "solidworks_source_bytes"


def verify_snapshot(source, snapshot, wire, native_rows):
    import convert.Commands.CheckRetained as validation

    wanted_steps = []
    for step in source.feature_timeline:
        if isinstance(step.definition, native_rows):
            fields = dict(step.definition.object_data)
            demand(type(fields.pop("record_data")) is bytes, "native source row lacks the replay copy")
            step = replace(step, definition=replace(step.definition, object_data=fields))
        wanted_steps.append(step)
    metadata = dict(source.metadata)
    metadata.pop(SOURCE)
    metadata[SNAPSHOT] = snapshot.metadata[SNAPSHOT]
    expected = replace(source, metadata=metadata, feature_timeline=tuple(wanted_steps))
    demand(snapshot.to_json() == expected.to_json() and b'"$bytes"' not in wire,
           "snapshot changed source ownership, tree, editable history or geometry, or retained wire bytes")
    validation.CheckRetained(snapshot)
    return len([step for step in wanted_steps if isinstance(step.definition, native_rows)])


def shifted_snapshot(snapshot):
    owned = snapshot.metadata[SNAPSHOT]
    return replace(snapshot, metadata=dict(snapshot.metadata) | {
        SNAPSHOT: {**owned, "written_at": owned["written_at"] + 1}
    })


def refusals(source, snapshot, routes, native_write):
    step, *rest = snapshot.feature_timeline
    stale = shifted_snapshot(snapshot)
    bad_row = replace(step, name=step.name + " altered")
    injection = replace(step, definition=replace(
        step.definition, object_data=dict(step.definition.object_data) | {"record_data": b"injected"}
    ))
    malformed_recipe = replace(snapshot, metadata=dict(snapshot.metadata) | {SNAPSHOT: {"locator": 5}})
    unqualified = replace(source, source=replace(source.source, format_id="kit-neutral"))
    bad_source = replace(source, metadata=dict(source.metadata) | {SOURCE: b"unbound"})
    changed_body = replace(snapshot, bodies=(replace(
        snapshot.bodies[0], topology=replace(snapshot.bodies[0].topology, volume=snapshot.bodies[0].topology.volume + 1)
    ),))
    cases = (
        (stale, "cold chamfer JSON readback differs from its regenerated part"),
        (replace(snapshot, feature_timeline=(bad_row, *rest)), "cold chamfer JSON readback differs"),
        (replace(snapshot, feature_timeline=(injection, *rest)), "cold chamfer JSON readback differs"),
        (malformed_recipe, "cold chamfer JSON recipe lacks its actual locator or epoch"),
        (unqualified, "native-only feature definitions cannot be exported"),
        (bad_source, "cold chamfer JSON requires its original source identity"),
        (changed_body, "cold chamfer JSON readback differs"),
    )
    for document, message in cases:
        for write in routes:
            target = BytesIO()
            reject(lambda: write(document, target), ValueError, message)
            demand(not target.getvalue(), "unverified snapshot altered its destination")
    sink = BytesIO()
    reject(lambda: native_write(changed_body, sink), ValueError, "cold chamfer JSON readback differs")
    demand(not sink.getvalue(), "changed snapshot reached the native writer destination")
    return len(cases) * len(routes) + 1


def sdk_worker(request):
    sys.path.insert(0, str(ROOT / "src"))
    audit = WriterAudit(ROOT / "src", HERE.parent / "ChmfJsonUnused.SLDPRT")
    sys.addaudithook(audit.observe)
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.json.Adapter import JsonAdapter
    from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import PrepChmfPart
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange import CadDocument
    from interchange.Features.FeatureKinds import NativeFeature
    for module in (
        "convert.Commands.CheckRetained", "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)
    for codec in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1", "cp1252"):
        lookup(codec)
    recipe, case = (request[key] for key in ("neutral", "case"))
    document = CadDocument.from_json(dumps(recipe["document"]))
    locator = {"final_destination": recipe["locator"]}
    values = locator | {OPTION: request["evidence"], "require_native_transfers": True}
    writer = SldprtWriter()
    adapter = JsonAdapter()

    def registry(model, target):
        return write_document(model, target, destination_format=JSON, allow_carrier=False)

    audit.phase = "cold"
    prepared = PrepChmfPart(document, BytesIO(), recipe["epoch"], WriteOptions(values=locator))
    raw = prepared.BytesValue
    demand({name: digest(data) for name, data in prepared.StreamsValue.items()} == case["streams"],
           "independent neutral generation changed the measured streams")
    source = open_document(raw, source_format=FORMAT, strict=True)
    targets = BytesIO(), BytesIO()
    outcomes = [write(source, target) for write, target in zip((registry, adapter.write), targets, strict=True)]
    wire = targets[0].getvalue()
    demand(wire == targets[1].getvalue() and all(value.application_usable and not value.dropped for value in outcomes),
           "direct and registry publication disagree")
    snapshot = open_document(wire, source_format=JSON, strict=True)
    rows = verify_snapshot(source, snapshot, wire, NativeFeature)
    repeated = BytesIO()
    registry(snapshot, repeated)
    demand(repeated.getvalue() == wire, "strict JSON reload changed canonical snapshot serialization")
    exact = digest(raw) == case["archive_sha256"]
    republished = check_public(snapshot, values, writer, write_document, WriteOptions, raw, case, exact)
    rejected = refusals(source, snapshot, (registry, adapter.write),
                        lambda model, target: writer.write(model, target, WriteOptions(values=values)))
    untouched = BytesIO()
    reject(lambda: write_document(source, untouched, destination_format="freecad.fcstd"), ValueError,
           "native-only feature definitions cannot be exported")
    demand(not untouched.getvalue() and not audit.denied and not audit.target_opens,
           "other-format refusal or archive comparison accessed an external input")
    audit.phase = "done"
    return {
        "source_sha256": digest(raw),
        "json_sha256": digest(wire),
        "ordered_rows": len(snapshot.feature_timeline),
        "native_rows": rows,
        "json_routes": len(outcomes),
        "native_republication_routes": republished,
        "sdk_refusals": rejected + 1,
        "runtime_input_reads": 0,
        "cad_launches": 0,
    }


def run_cli(*args):
    bootstrap = (
        "import sys; sys.path.insert(0, sys.argv.pop(1)); "
        "from convert.Commands.MainEntry import MainEntry; raise SystemExit(MainEntry())"
    )
    return run((sys.executable, "-I", "-B", "-c", bootstrap, str(ROOT / "src"), "convert", *map(str, args)),
               cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def check_cli(request, expected_sha):
    sys.path.insert(0, str(ROOT / "src"))
    from convert import open_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import PrepChmfPart
    from interchange import CadDocument
    from interchange.Features.FeatureKinds import NativeFeature

    recipe = request["neutral"]
    document = CadDocument.from_json(dumps(recipe["document"]))
    raw = PrepChmfPart(
        document, BytesIO(), recipe["epoch"], WriteOptions(values={"final_destination": recipe["locator"]}),
    ).BytesValue
    demand(digest(raw) == expected_sha, "CLI source differs from the guarded SDK source")
    with TemporaryDirectory(prefix="KitChmfJson.") as folder:
        area = Path(folder)
        original = area / PureWindowsPath(recipe["locator"]).name
        original.write_bytes(raw)
        output = area / "Snapshot.json"
        report = run_cli(original, output, "--json")
        demand(report.returncode == 0 and not report.stderr, report.stderr)
        cli = loads(report.stdout)
        wire = output.read_bytes()
        source = open_document(original, source_format=FORMAT, strict=True)
        snapshot = open_document(output, source_format=JSON, strict=True)
        rows = verify_snapshot(source, snapshot, wire, NativeFeature)
        repeated = area / "Repeated.json"
        again = run_cli(output, repeated, "--json")
        demand(again.returncode == 0 and not again.stderr and repeated.read_bytes() == wire,
               "ordinary CLI changed a qualified JSON snapshot")
        stale = area / "Stale.json"
        stale.write_text(shifted_snapshot(snapshot).to_json(), encoding="utf-8")
        refused = run_cli(stale, output, "--overwrite", "--json")
        unrelated = area / "Other.FCStd"
        other = run_cli(original, unrelated, "--json")
        demand(cli["destination_format"] == JSON and not cli["dropped"]
               and rows == 18 and refused.returncode == 1 and other.returncode == 1
               and "cold chamfer JSON readback differs" in refused.stderr
               and "NativeFeature" in other.stderr
               and original.read_bytes() == raw and output.read_bytes() == wire and not unrelated.exists(),
               "CLI accepted stale or unrelated state or changed a guarded path")
        return {"cli_publications": 2, "cli_refusals": 2, "cli_native_rows": rows}


def main():
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slot", type=int, choices=(0, 1))
    group.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(dumps(sdk_worker(loads(sys.stdin.read())), sort_keys=True))
        return
    request = build_request(args.slot)
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), cwd=ROOT,
                 input=dumps(request), text=True, capture_output=True, check=False, timeout=75)
    demand(result.returncode == 0 and not result.stderr, result.stderr)
    report = loads(result.stdout)
    print(dumps(report | check_cli(request, report["source_sha256"]), sort_keys=True))


if __name__ == "__main__":
    main()
