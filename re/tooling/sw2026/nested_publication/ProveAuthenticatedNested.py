from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from math import isclose
import json
from pathlib import Path, PureWindowsPath
import sys
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE.parent.parent), str(HERE.parent)]

from AuditNestedNeutralComposition import authored_document, checked
from MeasureNestedPublication import Audit, require, snapshot
from MeasurePublicNestedWriting import CASES
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks import SldprtAdapter
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.api.ApiContext import GetRegistry
from interchange.serialization.Deserialize import FromData


EVIDENCE = ROOT / "re/solidworks/measurements/2026"
MEASURED = EVIDENCE / "SdkMeasuredNestedPublication01.json"
MEASUREMENT_PIN = "66479552b24b577a3c0bff047efd39482255a1ed9f0af213d2b4dc8ab4bc8437"
OPTION = "solidworks_native_measurement"
DEFAULT = "SdkNestedDimensionedNative01"
REPEATED = "SdkRepeatedDimensionedNative01"
PREPARED = {
    DEFAULT: ("NeutralDimensioned.json", "ad22442a137e318ee27719adfe3f65df98397b59db73f7e663f0869bc18e9694"),
    REPEATED: ("NeutralRepeated.json", "7790b62dc9d3bdcd2757ff39c253f4b5ff73eddd86bc306936d6627e98b2ad3e"),
}
SUCCESS = ("measured",)
NEGATIVES = (
    "no-evidence", "wrong-native-report", "wrong-bundle", "wrong-epoch", "wrong-locator",
    "wrong-pose", "unqualified-location", "strict-deferred", "wrong-config", "fixed",
    "collision", "stream", "fault", "peer", "foreign-scoped-evidence",
)


def manifest_sha(files):
    return sha256(json.dumps(files, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def evidence(case, workspace=None):
    measured = json.loads(checked(MEASURED, MEASUREMENT_PIN))["cases"][case]
    if workspace is None:
        require(case in PREPARED, "the hosted neutral fixtures cover the two dimensioned bundles")
        filename, pin = PREPARED[case]
        recipe = json.loads(checked(EVIDENCE / "MeasuredNested" / filename, pin))
        document, native = FromData(recipe["neutral"]), recipe["native_destination"]
    else:
        folder = workspace / case
        packet = json.loads(checked(folder / "Packet.json", CASES[case]))
        fixture = json.loads(checked(folder / "Fixture.json", packet["fixture_sha256"]))
        authored = json.loads(checked(folder / "NeutralRequest.json", fixture["request_sha256"]))
        document, output = authored_document(authored)
        native = output["path_name"]
        require(output["saved_at"] == measured["written_at"] and measured["files"] == {
            row["file"]: {"bytes": row["bytes"], "sha256": row["sha256"]} for row in fixture["files"].values()
        }, "separate measured native and neutral writer authorities disagree")
    document.assert_valid()
    envelope = {
        "written_at": measured["written_at"],
        "receipt": {
            "schema": "kit.sw2026.rigid-nested-bundle-evidence.v1",
            "generated_manifest_sha256": manifest_sha(measured["files"]),
            "native_result_sha256": measured["oracle_terminal_sha256"],
        },
    }
    return document, native, envelope, measured


def differing_pose(document):
    graph = document.assembly
    occurrence = graph.instances[0]
    matrix = list(occurrence.transform.values)
    matrix[3] += 0.73
    pose = replace(occurrence, transform=replace(occurrence.transform, values=tuple(matrix)))
    edited = replace(document, assembly=replace(graph, instances=(pose, *graph.instances[1:])))
    edited.assert_valid()
    return edited


def readback(target, authored):
    result = open_document(target, strict=True)
    read, expected = result.assembly, authored.assembly
    require(read is not None and len(read.definitions) == len(expected.definitions)
            and len(read.instances) == len(expected.instances)
            and not read.mates and not read.mate_entities and not any(row.fixed for row in read.instances),
            "strict reader changed the native hierarchy membership or floating flags")
    names = {value.name for value in expected.definitions}
    require({value.name for value in read.definitions} == names,
            "strict reader did not join actual physical model titles")
    source_names = {row.id: row for row in expected.definitions}
    read_names = {row.id: row for row in read.definitions}
    source_by_name = {row.name: row for row in expected.definitions}
    for owner in read.definitions:
        old = source_by_name[owner.name]
        actual_rows, original_rows = read.GetChildren(owner.id), expected.GetChildren(old.id)
        require(len(actual_rows) == len(original_rows) and all(
            (one.order, one.name, read_names[one.definition_id].name, one.configuration_name)
            == (two.order, two.name, source_names[two.definition_id].name, two.configuration_name)
            and all(isclose(a, b, rel_tol=0.0, abs_tol=1e-12)
                    for a, b in zip(one.transform.values, two.transform.values, strict=True))
            for one, two in zip(actual_rows, original_rows, strict=True)
        ), "strict reader changed a named owned occurrence or its local placement")
    lengths = {}
    for row in read.definitions:
        require(row.configuration_name, "readback lost the selected configuration")
        if row.kind != "part":
            continue
        actual = next(value.document for value in read.documents if value.id == row.document_id)
        original = next(value.document for value in expected.documents if any(
            item.document_id == value.id and item.name == row.name for item in expected.definitions
        ))
        require(len(actual.parameters) == len(original.parameters)
                and sorted(round(value.value.value, 10) for value in actual.parameters)
                == sorted(round(value.value.value, 10) for value in original.parameters),
                "strict reader changed actual driving dimensions")
        lengths[row.name] = len(actual.parameters)
    return {"definitions": len(names), "instances": len(read.instances), "editable_leaf_driver_counts": lengths,
            "ordered_owned_placements": True}


def prove(case, mode, route, workspace):
    document, native, receipt, measured = evidence(case, workspace)
    files = measured["files"]
    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    with TemporaryDirectory(prefix="KitAuthNested") as tmp:
        area = Path(tmp).resolve()
        target = area / PureWindowsPath(native).name
        last = area / next(name for name in reversed(files) if name != target.name)
        options = {OPTION: deepcopy(receipt), "native_destination": native, "defer_native_delivery": True,
                   "require_native_transfers": True, "allow_carrier": mode != "strict-deferred"}
        configuration = "Unqualified" if mode == "wrong-config" else None
        destination = BytesIO(b"untouched stream") if mode == "stream" else target
        if mode == "no-evidence":
            del options[OPTION]
        elif mode == "wrong-native-report":
            options[OPTION]["receipt"]["native_result_sha256"] = "0" * 64
        elif mode == "wrong-bundle":
            options[OPTION]["receipt"]["generated_manifest_sha256"] = "0" * 64
        elif mode == "foreign-scoped-evidence":
            public = json.loads(checked(EVIDENCE / "SdkSealedPublicNestedParity03.json",
                                        "ef7105a0b13984cbdfe99ff3a419637c831f2cd89996d36924380dd526599bb2"))
            options[OPTION]["receipt"].update(
                generated_manifest_sha256=public["slots"][0]["routes"]["adapter"]["generated_artifact_manifest_sha256"],
                native_result_sha256=public["original_native_result_sha256"],
            )
        elif mode == "wrong-epoch":
            options[OPTION]["written_at"] += 1
        elif mode == "wrong-locator":
            options["native_destination"] = str(PureWindowsPath(r"C:\AnUnmeasuredNestedNamespace") / target.name)
        elif mode == "wrong-pose":
            document = differing_pose(document)
        elif mode == "unqualified-location":
            del options["defer_native_delivery"]
        elif mode == "collision":
            last.write_bytes(b"independently owned companion")
        elif mode == "fixed":
            graph = document.assembly
            occurrence = replace(graph.instances[0], fixed=True)
            document = replace(document, assembly=replace(graph, instances=(occurrence, *graph.instances[1:])))
        before = snapshot(area)
        audit_mode = {"fault": "publish-denied", "peer": "publish-race"}.get(mode, "fresh")
        _ = GetRegistry()
        audit = Audit(area, target, last, files, audit_mode)
        sys.addaudithook(audit.inspect)
        result, reason = None, None
        try:
            if route == "adapter":
                result = SldprtAdapter().write(document, destination, WriteOptions(configuration=configuration, values=options))
            else:
                result = write_document(document, destination, destination_format="solidworks.sldasm",
                                        configuration=configuration, allow_carrier=options["allow_carrier"], values=options)
        except (OSError, ValueError, TypeError, RuntimeError) as failure:
            reason = {"type": type(failure).__name__, "message": str(failure)}
        finally:
            audit.active = False
        after = snapshot(area)
        require(not audit.attempts, "writer read data or requested an external process: " + repr(audit.attempts))
        common = {"passed": True, "runtime_input_reads": 0, "native_processes_started": 0,
                  "stage_writes": len(audit.staged_write_attempts), "successful_native_flags": False}
        if mode in SUCCESS:
            require(reason is None and result is not None, "measured delivery failed: " + repr(reason))
            require(after == files and result.path == target and not result.dropped
                    and not result.vendor_loadable and not result.application_usable
                    and result.metadata["required_native_destination"] == native
                    and result.metadata["native_qualification"] == "measured_nested_deferred_delivery"
                    and sorted(str(row) for row in result.native_capabilities) == measured["native_transfers"],
                    "deferred publication did not reproduce every member or overstated native qualification")
            streams = sum(len(SldprtArchive.from_bytes(path.read_bytes()).streams) for path in area.iterdir())
            return {**common, "manifest_sha256": manifest_sha(after), "files": len(after), "streams": streams,
                    "native_transfers": measured["native_transfers"], "readback": readback(target, document)}
        require(result is None and reason, "unqualified publication returned a result")
        if mode == "peer":
            require(audit.injected and not target.exists() and set(after) == {last.name}
                    and last.read_bytes() == b"peer owns the last nested companion",
                    "nested bundle replaced a peer companion or retained a partial publication")
        else:
            require(after == before, "nested refusal did not restore destination state")
            if mode == "fault":
                require(len(audit.published) > 1 and reason["message"] == "controlled final companion failure",
                        "nested publication fault was not reached")
            else:
                require(not audit.staged_write_attempts, "unqualified nested request reached a staged file")
        if mode == "stream":
            require(destination.getvalue() == b"untouched stream", "nested refusal changed the caller stream")
        expected = {
            "no-evidence": "requires an offline native measurement receipt",
            "wrong-native-report": "requires authenticated offline evidence",
            "wrong-bundle": "requires authenticated offline evidence",
            "wrong-epoch": "does not match the exact generated bundle",
            "wrong-locator": "does not match the exact generated bundle",
            "wrong-pose": "does not match the exact generated bundle",
            "unqualified-location": "requires its measured location or explicit deferred delivery",
            "strict-deferred": "requires its measured location or explicit deferred delivery",
            "wrong-config": "requested assembly configuration is unavailable",
            "foreign-scoped-evidence": "different complete member count",
        }
        if mode in expected:
            require(expected[mode] in reason["message"], f"unexpected refusal for {mode}: {reason}")
        return {**common, "refused": reason["type"], "destination_preserved": True,
                **({"reason": expected[mode]} if mode in expected else {})}


def main():
    parser = ArgumentParser()
    parser.add_argument("--case", choices=CASES, default=DEFAULT)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--mode", choices=(*SUCCESS, *NEGATIVES), default="measured")
    parser.add_argument("--route", choices=("adapter", "registry"), default="registry")
    args = parser.parse_args()
    print(json.dumps(prove(args.case, args.mode, args.route, args.workspace), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
