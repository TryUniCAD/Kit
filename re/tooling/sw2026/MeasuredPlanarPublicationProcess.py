from argparse import ArgumentParser
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / "re/tooling/sw2026")]

from convert import open_document, write_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import PrepareAssembly
from convert.api.ApiContext import GetRegistry, KConvertEngine
from interchange.serialization.Deserialize import FromData
from MakeAssemblyBoundaryCase import make_case, make_perpendicular_case


FIXTURES = ROOT / "re/solidworks/measurements/2026/MeasuredPlanarPair"
MEASURED = "9eb6ee8e05d4cf357c4f0f0902604b6cf7f46d2e06c8fb6b05254d42c7a4cd5e"
OPTION = "solidworks_native_measurement"
POSITIVE = {"measured", "measured-explicit"}
LEGACY = {"legacy2", "legacy3", "legacy-perp", "legacy-perp-invalid"}
NEGATIVE = {
    "no-receipt", "forged-receipt", "wrong-member", "wrong-native-locator", "unmeasured-location",
    "strict-deferred", "wrong-config", "direct", "stream", "child-collision", "case-collision",
    "directory-collision", "dangling-child", "root-collision", "overwrite", "overwrite-empty",
    "missing-mapping", "wrong-mapping", "relative-mapping", "wrong-format", "unqualified-option",
    "unsupported-mate", "unqualified-child", "named-child", "commit-failure", "race-protection",
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def hashed(path, digest):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == digest, "disclosed fixture changed: " + path.name)
    return json.loads(raw)


def fixture():
    measured = hashed(FIXTURES / "MeasuredOutput.json", MEASURED)
    request = hashed(FIXTURES / "NeutralRequest.json", measured["neutral_request_sha256"])
    recovery = hashed(FIXTURES / "OriginalNativeRecovery.json", measured["native_recovery_sha256"])
    native = recovery["native_lifecycle"]
    require(recovery["passed"] and native["controls_healthy"] and native["ordered_distinct_lifetimes"]
            and native["tree_and_owner_signatures_retained"]
            and native["native_numeric_checks"] == 360 and native["native_process_count"] == 4,
            "published native evidence lacks the complete measured lifecycle")
    document = FromData(request["document"])
    document.assert_valid()
    return document, request["native_parent"], measured


def snapshot(folder):
    return {entry.name: ("symlink", os.readlink(entry)) if entry.is_symlink()
            else ("directory",) if entry.is_dir() else ("file", sha256(entry.read_bytes()).hexdigest())
            for entry in folder.iterdir()}


def metrics(payload):
    archive = SldprtArchive.from_bytes(payload)
    return {"bytes": len(payload), "sha256": sha256(payload).hexdigest(),
            "streams": {name: {"bytes": len(value), "sha256": sha256(value).hexdigest()}
                        for name, value in archive.streams.items()}}


@contextmanager
def audit_io(target, child, mode):
    enabled = False
    report = {"input_reads": [], "launches": [], "transaction_probe": False}
    code_roots = (ROOT / "src", Path(sys.base_prefix).resolve(), Path(sys.exec_prefix).resolve())
    access_flags = os.O_WRONLY | os.O_RDWR
    for name in ("utf-8", "utf-8-sig", "utf-16-le", "latin-1", "ascii"):
        "".encode(name)

    def gate(event, args):
        if not enabled:
            return
        if event == "open":
            item, _, flags = args
            if isinstance(item, int) or (flags & access_flags) == os.O_WRONLY:
                return
            path = Path(os.fsdecode(item)).resolve()
            if path.is_dir() or (path.suffix in (".py", ".pyc") and any(path.is_relative_to(root) for root in code_roots)):
                return
            report["input_reads"].append(str(path))
            raise PermissionError("unexpected input read")
        if event.startswith(("socket.", "subprocess.", "ctypes.", "winreg.")) or event in (
            "os.system", "os.posix_spawn", "os.fork", "os.exec",
        ):
            report["launches"].append(event)
            raise PermissionError("unexpected external writer operation")
        if event in ("os.rename", "os.link"):
            after = Path(args[1])
            if after == target and mode == "commit-failure":
                report["transaction_probe"] = "root"
            if after == target and mode == "race-protection" and not report["transaction_probe"]:
                with child.open("xb") as peer:
                    peer.write(b"peer-owned test data")
                report["transaction_probe"] = True
            if after == child and mode == "commit-failure" and report["transaction_probe"] == "root":
                report["transaction_probe"] = "raised"
                raise PermissionError("controlled second publication failure")

    sys.addaudithook(gate)
    enabled = True
    try:
        yield report
    finally:
        enabled = False
    require(not (report["input_reads"] or report["launches"]), "writer used an external input or process")


def changed_child(document, key):
    graph = document.assembly
    holder, = graph.documents
    child = holder.document
    if key == "unqualified-child":
        child = replace(child, metadata=child.metadata | {"unprojected": "text"})
    elif key == "named-child":
        first, *rest = child.parameters
        child = replace(child, parameters=(replace(first, name="FrameWidth"), *rest))
    else:
        boss, = child.feature_timeline
        (depth_id,) = boss.parameter_ids
        original = child.parameter(depth_id)
        edited = replace(original.value, value=original.value.value + 1.25)
        feature = replace(boss, definition=replace(boss.definition, length=edited))
        child = replace(child, feature_timeline=(feature,), parameters=tuple(
            replace(parameter, value=edited) if parameter.id == depth_id else parameter for parameter in child.parameters
        ))
    return replace(document, assembly=replace(graph, documents=(replace(holder, document=child),)))


def dimensional_readback(parent):
    document = open_document(parent, strict=True)
    graph = document.assembly
    require(len(graph.instances) == 2 and len(graph.mate_groups) == 1 and len(graph.mate_entities) == 4
            and tuple(str(mate.kind) for mate in graph.mates) == ("coincident", "distance")
            and tuple(row.fixed for row in graph.instances) == (True, False)
            and len(graph.documents) == 1, "strict readback changed the measured mate group")
    distance = graph.mates[1]
    parameters = graph.documents[0].document.parameters
    require(distance.value.value == 42.0 and len(parameters) == 3, "measured archive changed its driving length or child history")
    driver = document.parameter(distance.parameter_ids[0])
    require(driver.owner_id == distance.id and driver.value == distance.value, "distance driver lies outside its actual mate")
    deferred = KConvertEngine.read(
        parent, format_id="solidworks.sldasm",
        options=ReadOptions(strict=True, values={"resolve_components": False, "discover_companions": False}),
    )
    require(len(deferred.assembly.instances) == 2 and not deferred.assembly.documents
            and not deferred.assembly.mates and not deferred.parameters
            and any(value.format_id == "solidworks.mates" for value in deferred.brep_payloads)
            and deferred.metadata["solidworks.typed_mates_semantics"]["status"] == "deferred",
            "deferred child read exposed an unbound distance mate")
    return {"mates": 2, "distance_mm": distance.value.value,
            "child_parameters_mm": [row.value.value for row in parameters], "distance_driver": driver.name,
            "deferred_child_omits_unbound_parameter": True}


def legacy(mode, directory):
    doc = make_perpendicular_case(invalid=mode.endswith("invalid")) if mode.startswith("legacy-perp") else make_case(int(mode[-1]))
    target = directory / (doc.metadata["name"] + ".SLDASM")
    child = directory / (doc.assembly.documents[0].document.metadata["name"] + ".SLDPRT")
    native = "C:\\KitAssemblyBoundary\\" + target.name
    epoch, candidate, error = 1794001000, None, None
    with audit_io(target, child, mode):
        try:
            candidate = PrepareAssembly(doc, native, epoch, PublicProfile=True)
        except ValueError as failure:
            require(mode == "legacy-perp-invalid", str(failure))
        try:
            write_document(doc, target, allow_carrier=True, values={"native_destination": native, "portable": True})
        except (ValueError, LookupError) as failure:
            error = type(failure).__name__
        except Exception as failure:
            require(type(failure).__name__ == "AdapterNotFoundError", str(failure))
            error = type(failure).__name__
    require(error and not snapshot(directory), "unmeasured shape reached final publication")
    require((candidate is not None) is (mode != "legacy-perp-invalid"),
            "prior guarded shape construction changed")
    return {"passed": True, "runtime_input_file_reads": 0, "native_processes_started": 0,
            "writer_native_flags": False, "before": {}, "after": {}, "error": error,
            "generated_model_members": 2 if candidate is not None else 0,
            "generated_stream_counts": [] if candidate is None else [
                len(SldprtArchive.from_bytes(payload).streams)
                for payload in (candidate.BytesValue, candidate.ChildValue.BytesValue)
            ]}


def publication(mode, directory):
    doc, native, report = fixture()
    parent = directory / (doc.metadata["name"] + ".SLDASM")
    child = directory / (doc.assembly.documents[0].document.metadata["name"] + ".SLDPRT")
    values = {"native_destination": native, OPTION: deepcopy(report["measurement"]),
              "defer_native_delivery": True, "require_native_transfers": True}
    explicit = "solidworks.sldasm" if mode == "measured-explicit" else None
    stream = None
    overwrite = mode in {"overwrite", "overwrite-empty"}
    is_deferred = mode != "unmeasured-location"
    allow_carrier = mode != "strict-deferred"

    if mode == "no-receipt":
        del values[OPTION]
    elif mode == "forged-receipt":
        values[OPTION]["receipt"]["members"][0]["sha256"] = "1" * 64
    elif mode in ("wrong-member", "unqualified-child", "named-child"):
        doc = changed_child(doc, mode)
    elif mode == "wrong-native-locator":
        values["native_destination"] = "C:\\UnmeasuredAssemblyPath\\" + parent.name
    elif mode == "wrong-mapping":
        values["native_destination"] = "C:\\UnmeasuredAssemblyPath\\WrongBasename.SLDASM"
    elif mode == "relative-mapping":
        values["native_destination"] = parent.name
    elif mode == "missing-mapping":
        del values["native_destination"]
    elif mode == "wrong-format":
        explicit = "solidworks.sldprt"
    elif mode == "unqualified-option":
        values["recorded_fallback"] = True
    elif mode == "unsupported-mate":
        graph = doc.assembly
        first, second = graph.mates
        doc = replace(doc, assembly=replace(graph, mates=(replace(first, kind="parallel"), second)))
    elif mode == "stream":
        stream, explicit = BytesIO(b"protected stream"), "solidworks.sldasm"
    elif mode in ("child-collision", "case-collision"):
        (child if mode == "child-collision" else child.with_name(child.name.lower())).write_bytes(b"unrelated child")
    elif mode == "directory-collision":
        child.mkdir()
    elif mode == "dangling-child":
        child.symlink_to(directory / "missing")
    elif mode in ("root-collision", "overwrite"):
        parent.write_bytes(b"unrelated root")
    if not is_deferred:
        del values["defer_native_delivery"]
    if mode == "direct":
        values["final_destination"] = str(directory / "unowned-target" / parent.name)

    before = snapshot(directory)
    writer = GetRegistry().writer("solidworks.sldasm")
    info = writer.info
    require(info.format_id == "solidworks.sldprt" and info.extensions == (".sldprt", ".sldasm", ".slddrw")
            and info.aliases == ("solidworks.sldasm", "solidworks.slddrw")
            and info.part_extensions == (".sldprt",) and info.assembly_extensions == (".sldasm",)
            and not writer.supports(doc, parent.with_suffix(".SLDDRW")),
            "normal writer metadata changed format ownership")
    result, error = None, None
    with audit_io(parent, child, mode) as audit:
        try:
            if mode == "direct":
                result = writer.write(doc, parent, WriteOptions(values=values))
            else:
                result = write_document(doc, parent if stream is None else stream, destination_format=explicit,
                                        configuration="wrong" if mode == "wrong-config" else None, overwrite=overwrite,
                                        allow_carrier=allow_carrier, values=values)
        except Exception as failure:
            error = {"type": type(failure).__name__, "message": str(failure)}
    after = snapshot(directory)
    require(not any(name.startswith(".") for name in after), "failed transaction left a stage behind")
    outcome = {"passed": True, "runtime_input_file_reads": len(audit["input_reads"]),
               "native_processes_started": len(audit["launches"]), "before": before, "after": after,
               "writer_native_flags": False, "error": error, "whole_bundle_matches_native_input": False}
    if mode in POSITIVE:
        require(result is not None and error is None, repr(error))
        require(not result.vendor_loadable and not result.application_usable and not result.dropped
                and not result.carrier_capabilities and len(result.transferred_capabilities) == 9
                and result.path == parent.resolve() and result.metadata["component_file_count"] == 1
                and result.metadata["required_native_destination"] == native
                and result.metadata["native_qualification"] == "measured_planar_deferred_delivery",
                "alternate physical placement overstated native qualification")
        actual = {path.name: metrics(path.read_bytes()) for path in (parent, child)}
        require(actual == report["files"], "publication differs from exact full native measured pair")
        return {**outcome, "whole_bundle_matches_native_input": True,
                "matching_member_streams": sum(len(row["streams"]) for row in actual.values()),
                "readback": dimensional_readback(parent)}
    require(error is not None and result is None, "unmeasured, contradictory or unsafe publication succeeded")
    if mode == "race-protection":
        require(audit["transaction_probe"] is True and set(after) == {child.name}
                and child.read_bytes() == b"peer-owned test data", "stager did not retain the independent peer")
        return outcome | {"concurrent_companion_preserved": True}
    require(before == after, "a refused publication modified an existing entry")
    if mode == "commit-failure":
        require(audit["transaction_probe"] == "raised", "second publication failure was not exercised")
    if stream is not None:
        require(stream.getvalue() == b"protected stream", "assembly refusal modified the caller stream")
    if mode in {
        "no-receipt", "forged-receipt", "wrong-member", "wrong-native-locator",
        "unmeasured-location", "strict-deferred", "direct", "wrong-config",
    }:
        expected = {
            "no-receipt": "requires an offline native measurement receipt",
            "forged-receipt": "authenticated offline evidence",
            "wrong-member": "does not match the exact member",
            "wrong-native-locator": "different native locator",
            "unmeasured-location": "explicit deferred delivery",
            "strict-deferred": "explicit deferred delivery",
            "direct": "registry-owned stage",
            "wrong-config": "configuration is unavailable",
        }[mode]
        require(expected in error["message"], f"{mode} stopped at a different boundary: {error}")
    return outcome


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=sorted(POSITIVE | LEGACY | NEGATIVE))
    args = parser.parse_args()
    with TemporaryDirectory(prefix="KitMeasuredPlanar") as owned:
        directory = Path(owned).resolve()
        result = legacy(args.mode, directory) if args.mode in LEGACY else publication(args.mode, directory)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
