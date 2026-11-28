from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from AuditFreecadBoxReleases import read_box, require
from revolve.Preparation.RevolveStreamAudit02 import stream_audit
from units.CheckPublicDocumentUnits import expected, read


def digest(raw):
    return sha256(raw).hexdigest()


def checked(root, relative, wanted):
    path = root / relative
    require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(root), "evidence escaped its packet")
    raw = path.read_bytes()
    require(digest(raw) == wanted, f"changed release evidence: {relative}")
    return raw


def state(raw, generated, release, *, compact_keywords):
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    normal = read_box(raw, generated, release)
    public_units = read(raw, "solidworks.sldprt")["units"]
    require(public_units == expected("kg", 4), "public custom kilogram and precision read changed")
    archive = SldprtArchive.from_bytes(raw)
    critical, metadata = stream_audit(archive, ReadNativeLink(archive, 0), compact_keywords=compact_keywords)
    require(all(report["qualified"] for report in metadata.values()), "release version metadata is incomplete")
    return {
        "file_sha256": digest(raw), "normal_sdk_read": normal, "compact_keywords": compact_keywords,
        "normal_document_units": public_units, "exact_critical_streams": critical,
        "exact_version_metadata": metadata,
    }


def inspect(root, case, build, native):
    role = case["id"]
    initial = native["phases"][role + "/Generated"]
    reopened = native["phases"][role + "/FreshReopen"]
    for name, row in (("Generated", initial), ("FreshReopen", reopened)):
        checked(root, f"Inspection/{role}/{name}/Record.json", row["record_sha256"])
        require(row["passed"] and row["immutable_input"] and row["open_errors"] == row["open_warnings"] == 0,
                f"{role} lacks a clean native {name} phase")
    source = deepcopy(build["builds"][case["source_case"]]["generated"])
    release = case["source_case"].split("-")[1]
    generated = state(checked(root, case["input"], case["sha256"]), source, release, compact_keywords=False)
    require(initial["save_status"] == [True, 0, 0] and initial["signature"] == reopened["signature"],
            "release box native save changed actual feature ownership")
    names = case["parameter_names"]
    values = dict(case["dimensions_m"])
    values[names[-1]] = case["edit_values_m"][-1]
    require(initial["saved_dimensions_m"] == values, "native save retained the wrong parameter edits")
    source["source_dimensions_mm"] = [values[name] * 1000 for name in names]
    derivative = state(
        checked(root, f"Inspection/{role}/Generated/Edited.SLDPRT", initial["saved_sha256"]), source, release,
        compact_keywords=True,
    )
    return {
        "role": role,
        "source_release": release,
        "source_freecad_sha256": case["source_sha256"],
        "generated": generated,
        "saved_and_reopened": derivative,
        "native_state_counts": [len(initial["states"]), len(reopened["states"])],
        "native_checks": [initial["checks"], reopened["checks"]],
        "native_record_sha256": [initial["record_sha256"], reopened["record_sha256"]],
    }


def main():
    parser = ArgumentParser(description="Read exact FreeCAD release-box streams after native persistence")
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--native-sha256", required=True)
    parser.add_argument("--transport-sha256", required=True)
    args = parser.parse_args()
    root = args.packet.resolve(strict=True).parent
    packet = json.loads(checked(root, args.packet.name, args.packet_sha256))
    build = json.loads(checked(root, "BuildProof.json", packet["build_proof_sha256"]))
    native = json.loads(checked(root, "Inspection/Result.json", args.native_sha256))
    transport = json.loads(checked(root, "RootNativeTransport01/Result.json", args.transport_sha256))
    require(
        packet["schema"] == native["schema"] == "kit.sw2026.freecad-box-releases-native.v1"
        and native["packet_sha256"] == transport["packet_sha256"] == args.packet_sha256
        and transport["native_result_sha256"] == args.native_sha256
        and native["passed"] and native["controls_healthy"] and native["distinct_native_processes"] == 6
        and transport["passed"] and transport["inventory_unchanged"] and native["heldout_inputs_read"] == 0,
        "release box native lifecycle or custody is incomplete",
    )
    for role in ("ControlBefore", "ControlAfter"):
        control = native["phases"][role]
        require(control["passed"], "release box native control failed")
        checked(root, f"Inspection/{role}/Record.json", control["record_sha256"])
    result = {
        "schema": "kit.sw2026.freecad-release-box-native-readback.v1",
        "packet_sha256": args.packet_sha256,
        "native_result_sha256": args.native_sha256,
        "host_transport_sha256": args.transport_sha256,
        "qualifier_sha256": digest(Path(__file__).read_bytes()),
        "cases": [inspect(root, case, build, native) for case in packet["cases"]],
        "native_material_assignment_qualified": False,
        "complete_original_corpus_conversions": 0,
        "heldout_inputs_read": 0,
        "passed": True,
    }
    require(len(result["cases"]) == 2, "both measured FreeCAD releases are required")
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"passed": True, "cases": 2, "result_sha256": digest(args.output.read_bytes())}))


if __name__ == "__main__":
    main()
