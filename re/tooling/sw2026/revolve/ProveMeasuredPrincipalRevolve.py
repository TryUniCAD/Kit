from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from math import inf, nextafter
from os import O_RDWR, O_WRONLY
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument
from interchange.document.Behavior.DocumentIo import ToJson


def digest(data):
    return sha256(data).hexdigest()


def read_json(path):
    return loads(path.read_bytes())


def neutral(request):
    return CadDocument.from_json(dumps(request["document"]))


def stream_hashes(payload):
    streams = SldprtArchive.from_bytes(payload).streams
    assert len(streams) == 10
    return {name: digest(data) for name, data in sorted(streams.items())}


class WriterAudit:
    def __init__(self, output_dir):
        self.enabled = False
        self.allowed = output_dir
        self.file_reads = []
        self.launches = []
        self.output_opens = 0
        sys.addaudithook(self.observe)

    def observe(self, event, args):
        if not self.enabled:
            return
        if event in ("subprocess.Popen", "os.system", "socket.connect", "ctypes.dlopen"):
            self.launches.append(event)
            raise RuntimeError(event)
        if event == "import" and args[0].split(".")[0] in (
            "pythoncom", "pywintypes", "win32com", "FreeCAD", "adsk"
        ):
            self.launches.append(event)
            raise RuntimeError(args[0])
        if event == "open":
            path, _, flags = args
            if isinstance(path, (str, bytes)):
                value = Path(path if isinstance(path, str) else path.decode()).absolute()
                if value.is_relative_to(self.allowed):
                    if value.suffix.casefold() == ".sldprt" and flags & (O_WRONLY | O_RDWR):
                        self.output_opens += 1
                        return
                    if value.name.startswith(".") and ".kit-" in value.name and value.is_dir():
                        return
            self.file_reads.append(str(path))
            raise RuntimeError("external file open during writing")

    def run(self, call):
        self.enabled = True
        try:
            return call()
        finally:
            self.enabled = False

    def report(self):
        assert not self.file_reads and not self.launches
        return {"input_file_reads": 0, "external_launches": 0, "output_opens": self.output_opens}


def written(call, payload, sink=None):
    result = call()
    assert result.vendor_loadable and result.application_usable
    assert result.bytes_written == len(payload)
    assert result.metadata["solidworks_native_measurement"]["generated_sha256"] == digest(payload)
    if sink is not None:
        assert sink.getvalue() == payload


def denied(call, expected):
    try:
        call()
    except (ValueError, TypeError) as error:
        assert expected in str(error), (expected, str(error))
        return str(error)
    raise ValueError("unsupported output was published")


def mass_and_owners(document, expected, snapshot, with_brep):
    feature, = (item for item in document.feature_timeline if item.kind == "revolution")
    driver, = document.parameters
    sketch, = document.sketches
    selection, = document.selections
    body, = document.bodies
    support, = (item for item in document.support_planes if item.id == sketch.support_plane_id)
    original, = expected.feature_timeline
    assert support.name == expected.support_planes[0].name
    assert sketch.attributes["support_plane_source"] == "plane-reference"
    assert (driver.owner_id, driver.name, driver.value) == (feature.id, "D1", expected.parameters[0].value)
    assert feature.definition.AxisDirection == original.definition.AxisDirection
    assert feature.definition.AxisOrigin == original.definition.AxisOrigin
    assert feature.definition.AlongParameterId == driver.id
    assert feature.definition.AxisSelectionId == selection.id
    assert selection.path[0].entity_id == sketch.id and selection.path[-1].entity_id == sketch.entities[-1].id
    assert sketch.entities[-1].construction and len(sketch.constraints) == 4
    assert body.final_feature_id == feature.id
    topo = body.topology
    assert (document.brep is not None) is with_brep
    if with_brep:
        assert body.name == original.name
        assert (topo.solid_count, topo.shell_count, topo.face_count, topo.edge_count, topo.vertex_count) == (1, 1, 6, 12, 8)
        assert format(topo.volume / 1e9, ".6g") == format(snapshot["mass"]["volume"], ".6g")
        assert format(topo.surface_area / 1e6, ".6g") == format(snapshot["mass"]["area"], ".6g")
    else:
        assert body.name == "Body 1" and topo.face_count == 0
        assert topo.volume is None and topo.surface_area is None


def prove_revolve(args, scratch):
    packet = args.native_packet
    summary_path = ROOT / "re/solidworks/measurements/2026/SdkPrincipalRevolveMacNative01.json"
    paths = {"summary": summary_path, "native_result": packet / "Oracle/Inspection.json", "inspection_job": packet / "InspectJob.json"}
    evidence = {key: path.read_bytes().decode("utf-8") for key, path in paths.items()}
    request = read_json(args.neutral[args.worker])
    source = loads(evidence["inspection_job"])["cases"][args.worker]
    name = PureWindowsPath(source["source"]).name
    reference_path = packet / "Candidates" / name
    reference = reference_path.read_bytes()
    assert digest(reference) == source["sha256"]
    native_row, = (row for row in loads(evidence["summary"])["cases"].values() if row["generated_sha256"] == source["sha256"])
    document = neutral(request)
    envelope = {"written_at": request["epoch"], "receipt": evidence}
    values = {"final_destination": source["source"], "solidworks_native_measurement": envelope}
    variants = {"authored": document}
    for role, full in (("full", True), ("design", False)):
        from_path = open_document(reference_path, strict=True, include_brep=full)
        from_stream = open_document(BytesIO(reference), source_format="solidworks.sldprt", strict=True, include_brep=full)
        for form, model in (("path", from_path), ("stream", from_stream)):
            restored = CadDocument.from_json(ToJson(model, IndentSize=None))
            mass_and_owners(restored, document, native_row["phases"]["open"], full)
            variants[f"{role}_{form}_json"] = restored
    wrong_target = scratch / "unmeasured" / name
    wrong_target.parent.mkdir()
    wrong_target.write_bytes(b"preserve")
    direct = SldprtWriter()
    GetDocumentCaps(document)
    lookup("utf-16-le")
    audit = WriterAudit(scratch)
    passed = []
    for role, model in variants.items():
        for method in ("direct", "registry"):
            sink = BytesIO()
            if method == "direct":
                call = lambda: direct.write(model, sink, WriteOptions(values=values))
            else:
                call = lambda: write_document(model, sink, destination_format="solidworks.sldprt", values=values)
            written(lambda: audit.run(call), reference, sink)
            passed.append(role + "_" + method)

    changed_driver = replace(document.parameters[0], value=replace(document.parameters[0].value, value=nextafter(document.parameters[0].value.value, inf)))
    changed_document = replace(document, parameters=(changed_driver,))
    edited_source = replace(variants["design_path_json"], metadata={**variants["design_path_json"].metadata, "extra_native_owner": 42})
    misses = (
        ("missing_receipt", document, {}, "offline native"),
        ("edited_summary", document, {**values, "solidworks_native_measurement": {**envelope, "receipt": {**evidence, "summary": evidence["summary"] + "\n"}}}, "authenticated"),
        ("edited_native_terminal", document, {**values, "solidworks_native_measurement": {**envelope, "receipt": {**evidence, "native_result": evidence["native_result"] + "\n"}}}, "authenticated"),
        ("edited_job", document, {**values, "solidworks_native_measurement": {**envelope, "receipt": {**evidence, "inspection_job": evidence["inspection_job"] + "\n"}}}, "authenticated"),
        ("stale_epoch", document, {**values, "solidworks_native_measurement": {**envelope, "written_at": request["epoch"] + 1}}, "no matching native measurement"),
        ("original_windows_locator_from_mac", document, {**values, "final_destination": request["locator"]}, "exact inspected self locator"),
        ("changed_driver_one_ulp", changed_document, values, "no matching native measurement"),
        ("changed_source_metadata", edited_source, values, "differs from its regenerated part"),
    )
    negatives = {}
    for role, model, options, error in misses:
        sink = BytesIO()
        negatives[role] = denied(lambda: audit.run(lambda: direct.write(model, sink, WriteOptions(values=options))), error)
        assert sink.tell() == 0 and not sink.getvalue()
    for method in ("direct", "registry"):
        populated = BytesIO(b"preserve")
        populated.seek(2)
        if method == "direct":
            call = lambda: direct.write(document, populated, WriteOptions(values=values))
            write_bad_path = lambda: direct.write(document, wrong_target, WriteOptions(overwrite=True, values=values))
        else:
            call = lambda: write_document(document, populated, destination_format="solidworks.sldprt", values=values)
            write_bad_path = lambda: write_document(document, wrong_target, overwrite=True, values=values)
        negatives[method + "_populated_stream"] = denied(lambda: audit.run(call), "empty")
        negatives[method + "_wrong_physical_locator"] = denied(lambda: audit.run(write_bad_path), "differs from its inspected locator")
        assert populated.getvalue() == b"preserve" and populated.tell() == 2
        assert wrong_target.read_bytes() == b"preserve" and list(wrong_target.parent.iterdir()) == [wrong_target]

    old_values = {"final_destination": request["locator"]}
    old = audit.run(lambda: PrepareRevolve(document, BytesIO(), request["epoch"], WriteOptions(values=old_values)).BytesValue)
    assert reference_path.read_bytes() == reference
    return {
        "case": "revolve_" + str(args.worker), "generated_sha256": digest(reference),
        "bytes": len(reference), "stream_sha256": stream_hashes(reference), "positive_paths": passed,
        "refusals": negatives, "runtime": audit.report(), "strict_modes": 4,
        "macos_original_windows_locator": {"bytes": len(old), "sha256": digest(old)},
        "protected_inputs": 0, "oracle_launches": 0,
    }


def prove_plain(args, scratch):
    role = ("Skew", "Step")[args.worker - 2]
    packet = args.plain_packet / role
    request = read_json(packet / "SdkRequest.json")
    document = neutral(request)
    target = scratch / PureWindowsPath(request["expected_locator"]).name
    native = packet / target.name
    reference = native.read_bytes()
    summary = read_json(ROOT / "re/solidworks/measurements/2026/SdkDefaultPartNative01.json")
    build, = (row for row in summary["builds"] if row["role"] == role)
    assert digest(reference) == build["candidate_sha256"] and len(reference) == build["bytes"]
    values = {"solidworks_native_measurement": {"written_at": request["written_at"], "receipt": summary}}
    GetDocumentCaps(document)
    lookup("utf-16-le")
    audit = WriterAudit(scratch)
    written(lambda: audit.run(lambda: write_document(document, target, values=values)), reference)
    assert target.read_bytes() == reference
    reread = open_document(target, strict=True)
    assert reread.brep is not None and reread.bodies[0].topology.solid_count == 1
    sink = BytesIO()
    stream_values = {**values, "final_destination": request["expected_locator"]}
    written(lambda: audit.run(lambda: SldprtWriter().write(reread, sink, WriteOptions(values=stream_values))), reference, sink)
    return {"case": role, "generated_sha256": digest(reference), "bytes": len(reference), "stream_sha256": stream_hashes(reference), "positive_paths": ["inferred_registry_file", "strict_readback_direct_stream"], "runtime": audit.report(), "oracle_launches": 0}


def source_fingerprint():
    listed = check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "src"], cwd=ROOT)
    files = sorted(set(name for name in listed.split(b"\0") if name))
    result = sha256()
    for name in files:
        result.update(name + b"\0" + sha256((ROOT / name.decode("utf-8")).read_bytes()).digest())
    return {"files": len(files), "sha256": result.hexdigest()}


def main():
    parser = ArgumentParser()
    parser.add_argument("--native-packet", type=Path, required=True)
    parser.add_argument("--plain-packet", type=Path, required=True)
    parser.add_argument("--neutral", nargs=2, type=Path, required=True)
    parser.add_argument("--worker", type=int, choices=range(4))
    args = parser.parse_args()
    if args.worker is not None:
        with TemporaryDirectory(prefix="KitMeasuredPrincipalRevolve-") as temp:
            scratch = Path(temp).resolve()
            method = prove_revolve if args.worker < 2 else prove_plain
            print(dumps(method(args, scratch)))
        return
    rows = [
        loads(check_output([sys.executable, "-I", "-B", str(Path(__file__).resolve()), *sys.argv[1:], "--worker", str(index)]))
        for index in range(4)
    ]
    print(dumps({
        "schema": "kit.sw2026.measured-principal-revolve-public.v1",
        "script_sha256": digest(Path(__file__).read_bytes()),
        "native_summary_sha256": digest((ROOT / "re/solidworks/measurements/2026/SdkPrincipalRevolveMacNative01.json").read_bytes()),
        "records": rows, "fresh_workers": len(rows), "new_native_processes": 0, "new_heldout_credit": 0, "source_fingerprint": source_fingerprint()
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
