from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from json import dumps, loads
from os import O_ACCMODE, O_WRONLY, fsdecode
from pathlib import Path
from tempfile import TemporaryDirectory
import sys


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "re/solidworks/measurements/2026/MeasuredPlanarPair"
PARENT = "PublicPlanarPair2.SLDASM"
CHILD = "PublicDatumPrism.SLDPRT"
MEASUREMENT_SHA = "9eb6ee8e05d4cf357c4f0f0902604b6cf7f46d2e06c8fb6b05254d42c7a4cd5e"


def verified(path, digest):
    payload = path.read_bytes()
    if sha256(payload).hexdigest() != digest:
        raise ValueError(f"measured planar evidence changed at {path.name}")
    return loads(payload)


def check_report(packet, expected, recovery):
    receipt = expected["measurement"]["receipt"]
    fixture = verified(packet / "Fixture.json", receipt["fixture_sha256"])
    recipe = verified(packet / "Recipe.json", receipt["packet_sha256"])
    native = recovery["native_lifecycle"]
    assert recovery["passed"] and native["controls_healthy"]
    assert fixture["files"] == expected["files"]
    assert fixture["request_sha256"] == expected["neutral_request_sha256"]
    assert recipe["fixture_sha256"] == receipt["fixture_sha256"]
    assert recipe["order"][:4] == ["before", "generated", "reopen", "after"]
    assert native["oracle_sha256"] == receipt["oracle"]["sha256"]
    assert native["oracle_version"] == receipt["oracle"]["build"]
    assert native["native_numeric_checks"] == 360
    for phase in receipt["phases"]:
        role = phase["mode"]
        observed = native["phases"][role]
        wrapper = verified(packet / "Inspection" / role / "Record.json", phase["record_sha256"])
        result = wrapper["result"]
        identity = result["oracle_identity"]
        assert wrapper["passed"] and result["passed"] and phase["passed"]
        for key in ("started_at", "finished_at", "open_errors", "open_warnings"):
            assert result[key] == phase[key]
        for key in ("process_id", "process_creation_filetime"):
            assert identity[key] == observed[key] == phase[key]
        if role == "generated":
            assert wrapper["job"]["input"] == {
                "parent": fixture["files"][PARENT]["sha256"],
                "child": fixture["files"][CHILD]["sha256"],
            }


def write_guarded(document, options, target, writer):
    attempts = []
    enabled = False
    allowed = (ROOT / "src", Path(sys.base_prefix).resolve(), Path(sys.exec_prefix).resolve())
    for name in ("utf-8", "utf-8-sig", "utf-16-le", "latin-1", "ascii"):
        lookup(name)

    def guard(event, items):
        if not enabled:
            return
        if event.startswith("socket.") or event == "subprocess.Popen":
            attempts.append(event)
            raise PermissionError(event)
        if event != "open":
            return
        value, _, flags = items
        if isinstance(value, int) or flags & O_ACCMODE == O_WRONLY:
            return
        path = Path(fsdecode(value)).resolve()
        if path.is_relative_to(target.parent) and path.is_dir():
            return
        if path.suffix in (".py", ".pyc") and any(path.is_relative_to(base) for base in allowed):
            return
        attempts.append(str(path))
        raise PermissionError(f"unexpected native writer input read at {path}")

    sys.addaudithook(guard)
    enabled = True
    try:
        result = writer(document, target, allow_carrier=False, values=options)
    finally:
        enabled = False
    assert result.application_usable and result.vendor_loadable and not result.dropped
    assert not attempts
    return len(attempts)


def inspect_pair(parent, reader):
    result = reader(parent, strict=True)
    graph = result.assembly
    assert graph is not None and len(graph.mate_groups) == 1
    assert len(graph.instances) == 2 and len(graph.mate_entities) == 4
    assert tuple(str(value.kind) for value in graph.mates) == ("coincident", "distance")
    assert graph.mates[1].value is not None and graph.mates[1].value.value == 42.0
    assert result.metadata["solidworks.typed_mates_semantics"]["status"] == "admitted"
    assert tuple(value.fixed for value in graph.instances) == (True, False)
    parameters = graph.documents[0].document.parameters
    assert len(parameters) == 3
    return {
        "occurrences": len(graph.instances),
        "mates": len(graph.mates),
        "endpoints": len(graph.mate_entities),
        "child_drivers_mm": [value.value.value for value in parameters],
        "mate_distance_mm": graph.mates[1].value.value,
    }


def archive_metrics(payload, archive_type):
    streams = archive_type.from_bytes(payload).streams
    return {
        "bytes": len(payload),
        "sha256": sha256(payload).hexdigest(),
        "streams": {
            name: {"bytes": len(value), "sha256": sha256(value).hexdigest()}
            for name, value in streams.items()
        },
    }


def prove(packet):
    sys.path.insert(0, str(ROOT / "src"))
    from convert import open_document, write_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from interchange.document.Models.DocumentModel import CadDocument

    expected = verified(FIXTURES / "MeasuredOutput.json", MEASUREMENT_SHA)
    request = verified(FIXTURES / "NeutralRequest.json", expected["neutral_request_sha256"])
    recovery = verified(FIXTURES / "OriginalNativeRecovery.json", expected["native_recovery_sha256"])
    check_report(packet, expected, recovery)
    doc = CadDocument.from_json(dumps(request["document"]))
    options = {
        "native_destination": request["native_parent"],
        "solidworks_native_measurement": expected["measurement"],
        "require_native_transfers": True,
    }
    with TemporaryDirectory(prefix="KitMeasuredPlanar") as directory:
        parent = Path(directory).resolve() / PARENT
        attempted = write_guarded(doc, options, parent, write_document)
        metrics = {
            name: archive_metrics((parent.parent / name).read_bytes(), SldprtArchive)
            for name in (CHILD, PARENT)
        }
        assert metrics == expected["files"]
        typed = inspect_pair(parent, open_document)
    return {
        "schema": "kit.sw2026.planar-main-registry-proof.v1",
        "measured_output_sha256": MEASUREMENT_SHA,
        "runtime_input_file_reads": attempted,
        "native_processes_started": 0,
        "native_numeric_checks_in_original_receipt": 360,
        "matching_generated_files": len(metrics),
        "matching_generated_streams": sum(len(row["streams"]) for row in metrics.values()),
        "member_sha256": {name: row["sha256"] for name, row in metrics.items()},
        "strict_public_read": typed,
        "passed": True,
    }


def main():
    cli = ArgumentParser()
    cli.add_argument("--packet", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    result = prove(args.packet)
    with args.output.open("x", encoding="utf-8") as file:
        file.write(dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
