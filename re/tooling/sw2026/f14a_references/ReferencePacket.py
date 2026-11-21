from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path, PureWindowsPath
import json


SCHEMA = "kit.sw2026.f14a-live-references.v2"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
PRIOR = "bfad084b837281083c6550f20a2fc8c2139bef428c79c59aa7b8082a4a1c94ca"
PRIOR_WINDOWS = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover\FreecadNewerReleaseNative01")
CASES = ("Freecad102", "Freecad114")
DRIVERS = ("Length@AdditiveBox Profile", "Width@AdditiveBox Profile", "Height@AdditiveBox")
BASELINE_M = (0.02, 0.03, 0.01)
EDIT_HEIGHT_M = (0.01587, 0.01619)
CAPTURE_AUDIT = "F14aLiveReferenceCapture01.json"
PREVIOUS_CAPTURE = "6bc759f108d1d4da3c771ec1841f2c70e868c8c1a68cb9934fd71a7de5d4d7f3"
RECEIPTS = {
    "SdkFreecadBoxReleaseNative01.json": "e87ae3d9520edcffd262b1dc2457b2bd4e5a70fe4ff34c1a1271079d5628b856",
    "SdkFreecadF14aTopologyLineage01.json": "ff4edb3b60ebc6d76714f14c56210acc7be2dd5fc9025042e5c2f6bf80bd6266",
    "DrawingEdgeApiMetadata01.json": "4ec29582a96d7e6d76464814d46e817ccb55bbf870be4e39dd21be05e3cee0af",
    CAPTURE_AUDIT: "a0b4956500809b340769fea5b1cb882212fc72c6f9c83f217a5b70aad102cd59",
}
TOOLS = ("ReferencePacket.py", "RunLiveReferences.py", "ReferenceApi.py", "ReferenceTopology.py", "ReferenceControl.py", "BoxTopology.py")


class EvidenceFailure(ValueError):
    pass


def require(condition, detail):
    if not condition:
        raise EvidenceFailure(detail)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def checked(root, relative, expected):
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve(strict=True).is_relative_to(root)
            and digest(path) == expected, f"changed disclosed packet member: {relative}")
    return path


def read(root, relative, expected):
    return json.loads(checked(root, relative, expected).read_bytes())


def verify_oracle(identity):
    require(identity["version_matches"] and identity["file_version"] == "34.5.2.0604"
            and identity["sha256"] == ORACLE and identity["pe_machine"] == "0x8664", "unexpected SOLIDWORKS oracle image")
    return identity["process_id"], identity["process_creation_filetime"]


def bind_prior(prior, native, lineage):
    job = read(prior, "Packet.json", PRIOR)
    require(native["packet_sha256"] == PRIOR and native["oracle_executable_sha256"] == job["oracle_sha256"] == ORACLE
            and native["scoped_native_lifecycle_passed"] and native["heldout_inputs_read"] == job["heldout_inputs_read"] == 0
            and lineage["protected_inputs_read"] == 0 and not lineage["native_reference_persistence_qualified"],
            "prior release or lineage scope changed")
    require(tuple(case["id"] for case in job["cases"]) == tuple(row["role"] for row in native["cases"]) == CASES,
            "unexpected disclosed model cohort")
    terminal = read(prior, "Inspection/Result.json", native["native_result_sha256"])
    require(terminal["passed"] and terminal["controls_healthy"] and terminal["distinct_native_processes"] == 6,
            "prior native lifecycle is unqualified")
    seed = checked(prior, "Control.SLDPRT", job["control_sha256"])
    api = read(prior, "DocumentUnitApi.json", job["api_sha256"])
    checked(prior, "BuildProof.json", job["build_proof_sha256"])
    require({path.name for path in (prior / "Tools").glob("*.py")} == set(job["tools_sha256"]),
            "the prior native observer directory has an unbound Python tool")
    for name, expected in job["tools_sha256"].items():
        checked(prior, Path("Tools") / name, expected)
    for role in ("ControlBefore", "ControlAfter"):
        phase = terminal["phases"][role]
        require(phase["passed"] and phase["record_sha256"] == native["healthy_control_records_sha256"][role],
                "prior bracket lacks its exact accepted native record")
        checked(prior, Path("Inspection") / role / "Record.json", phase["record_sha256"])
    bound = []
    for case, previous, edited_height in zip(job["cases"], native["cases"], EDIT_HEIGHT_M, strict=True):
        name = case["id"]
        geometry = lineage["cases"][name]
        source_rel = Path("Inputs") / name / "F14a.SLDPRT"
        require(Path(case["input"]) == source_rel and case["sha256"] == previous["generated"]["file_sha256"] ==
                geometry["generated_sha256"] and case["source_sha256"] == previous["source_freecad_sha256"] ==
                geometry["source"]["original_sha256"] and not geometry["generated_native_boundary_identities_present"],
                "cold source or model-only provenance changed")
        source = checked(prior, source_rel, case["sha256"])
        edited_sha = previous["saved_and_reopened"]["file_sha256"]
        require(edited_sha == geometry["saved_sha256"], "prior edited save has another lineage")
        inspected = Path("Inspection") / name
        prior_edited = inspected / "Generated" / "Edited.SLDPRT"
        checked(prior, prior_edited, edited_sha)
        phases = []
        for role, file_sha, file_rel, record_sha in zip(
                ("Generated", "FreshReopen"), (case["sha256"], edited_sha), (source_rel, prior_edited),
                previous["native_record_sha256"], strict=True):
            row = read(prior, inspected / role / "Record.json", record_sha)
            state = row["result"]
            actual_path = next(item["result"] for item in row["api_calls"] if item["method"] == "GetPathName")
            published = terminal["phases"][name + "/" + role]
            require(state["passed"] and state["immutable_input"] and not row["first_failure"] and not row["cleanup_errors"] and
                    published["passed"] and published["record_sha256"] == record_sha and
                    row["job"] == {"role": role, "input_sha256": file_sha} and
                    PureWindowsPath(actual_path) == PRIOR_WINDOWS / PureWindowsPath(file_rel),
                    "prior exact original, edited, or reopened locator changed")
            verify_oracle(state["oracle_identity"])
            phases.append(state)
        generated, reopened = phases
        dimensions = case["dimensions_m"]
        edited = dimensions | {DRIVERS[-1]: edited_height}
        require(tuple(case["parameter_names"]) == DRIVERS and tuple(dimensions[key] for key in DRIVERS) == BASELINE_M
                and generated["saved_dimensions_m"] == edited and generated["saved_sha256"] == edited_sha
                and generated["save_status"] == [True, 0, 0] and generated["signature"] == reopened["signature"]
                and generated["roles"] == reopened["roles"], "prior exact edit or actual parameter owner changed")
        bound.append({"case": case, "source": source, "edited": edited, "prior_roles": generated["roles"],
                      "prior_signature": generated["signature"], "prior_sha256": previous["native_record_sha256"],
                      "prior_edited_sha256": edited_sha, "prior_units": generated["states"]["Initial"]["document_units"],
                      "unit_api": api})
    return seed, api, bound


def load_receipts(root):
    audit = read(root, CAPTURE_AUDIT, RECEIPTS[CAPTURE_AUDIT])
    previous = audit["failed_f14a_capture"]
    require(previous["result_sha256"] == PREVIOUS_CAPTURE and not previous["passed"] and
            previous["capture_guard_refusals"] == 216 and previous["resolved_reference_calls"] == 0 and
            audit["independent_native_byte_transport"]["observed_return_types"] == {"memoryview": 56},
            "previous failed capture or independent transport evidence changed")
    return tuple(read(root, name, expected) for name, expected in RECEIPTS.items() if name != CAPTURE_AUDIT)


def verify(packet, expected, prior):
    root = packet.parent.resolve(strict=True)
    job = read(root, packet.name, expected)
    require(job["schema"] == SCHEMA and job["prior_sha256"] == PRIOR and job["receipts_sha256"] == RECEIPTS
            and set(job["tools_sha256"]) == set(TOOLS), "live-reference packet scope differs")
    require({path.name for path in (root / "Tools").glob("*.py")} == set(TOOLS), "the live-reference tool directory changed")
    for name, wanted in job["tools_sha256"].items():
        checked(root, Path("Tools") / name, wanted)
    require(Path(__file__).parent.resolve() == root / "Tools", "run the manifest-bound live-reference tooling")
    native, lineage, metadata = load_receipts(root)
    seed, api, bound = bind_prior(prior.resolve(strict=True), native, lineage)
    return job, seed, api, bound, metadata


def stage(prior, destination):
    sources = Path(__file__).parent.resolve()
    receipts = sources.parents[2] / "solidworks/measurements/2026"
    native, lineage, _ = load_receipts(receipts)
    bind_prior(prior.resolve(strict=True), native, lineage)
    paths = {name: sources / name for name in TOOLS}
    paths["BoxTopology.py"] = sources.parent / "f14a_lineage" / "BoxTopology.py"
    tool_data = {name: path.read_bytes() for name, path in paths.items()}
    job = {"schema": SCHEMA, "prior_sha256": PRIOR, "receipts_sha256": RECEIPTS,
           "tools_sha256": {name: sha256(data).hexdigest() for name, data in tool_data.items()}}
    destination.mkdir(exist_ok=False)
    (destination / "Tools").mkdir()
    for name, data in tool_data.items():
        (destination / "Tools" / name).write_bytes(data)
    for name, wanted in RECEIPTS.items():
        (destination / name).write_bytes(checked(receipts, name, wanted).read_bytes())
    packet = destination / "Probe.json"
    packet.write_text(json.dumps(job, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return {"packet": str(packet), "sha256": digest(packet), "native_processes_started": 0, "copied_cad_files": 0}


if __name__ == "__main__":
    parser = ArgumentParser(description="Freeze the disclosed F14a live-reference measurement tooling")
    parser.add_argument("prior", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(stage(args.prior, args.destination), sort_keys=True))
