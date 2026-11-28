from codecs import lookup
from hashlib import sha256
from importlib import import_module
from json import loads
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
NATIVE_RECORD = "re/solidworks/measurements/2026/GeneratedRotatedMateNative01.json"
RECEIPT_SHA = "dd062a6526c9fb74aad7e8425fa9c8f585ca9929c27d2ed1836271392ed02aff"
PARENT = "A22CombinedRotated.SLDASM"
CHILD = "CohortChild.SLDPRT"
FORMAT = "solidworks.sldasm"
ORDER = ("ControlBefore", "Generated", "Reopen", "ControlAfter")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finger(value):
    return {"bytes": len(value), "sha256": sha256(value).hexdigest()}


def read_bound(path, expected):
    require(path.is_file() and not path.is_symlink(), f"missing exact disclosed file {path.name}")
    raw = path.read_bytes()
    require(finger(raw)["sha256"] == expected, f"changed exact disclosed file {path.name}")
    return raw


def load_bound(path, expected):
    return loads(read_bound(path, expected))


def paired_inputs(packet, receipt):
    generation, native, source = (receipt[key] for key in ("generation", "native", "source"))
    build = load_bound(packet / "SanitizedGenerationT01.json", generation["guarded_report_sha256"])
    freeze = load_bound(packet / "WriterFrozenT01/FrozenSource.json", generation["source_manifest_sha256"])
    raw = load_bound(packet / "InspectionT01/Result.json", native["result_sha256"])
    trial = load_bound(packet / "PairedTrialT01.json", generation["paired_packet_sha256"])
    lock = load_bound(packet / "GenerationFreezeT01.json", trial["generation_freeze_sha256"])
    request = load_bound(packet / "GeneratedRequestT01.json", generation["request_sha256"])
    source_trial = load_bound(packet / "Trial.json", source["packet_sha256"])
    source_result = load_bound(packet / "Native/SourceEvidence.json", source["native_result_sha256"])
    require(receipt["passed"] and receipt["heldout_inputs_read"] == 0 and raw["passed"]
            and raw["controls_healthy"] and raw["source_bracket_identity"]
            and raw["immutable_inputs_unchanged"] and raw["edit_identity_preserved"]
            and raw["reopen_identity_preserved"] and raw["source_generated_checks"] == native["comparisons"]
            and all(raw["source_generated_checks"].values()) and raw["packet_sha256"] == generation["paired_packet_sha256"]
            and source_result["passed"] and source_result["packet_sha256"] == source["packet_sha256"]
            and source_trial["oracle_sha256"] == receipt["oracle"]["sha256"]
            and freeze["base"] == trial["writer_revision"] == lock["writer_revision"] == generation["writer_revision"]
            and freeze["file_count"] == generation["source_file_count"] == len(freeze["files_sha256"])
            and set(lock) <= set(generation) and all(lock[key] == generation[key] for key in lock)
            and build["input_runtime_file_access_attempts"] == 0 and build["writer_output_count"] == 2
            and set(build["inspection"]["logical_round_trips"]) == {
                "Contents/Config-0", "Contents/Config-0-ResolvedFeatures", "Contents/Config-0-MatesList",
                "Header2", "Contents/Config-0-ModelHeader", "Contents/CMgr", "Contents/Definition",
            }, "native and independently generated provenance disagree")
    inputs = {
        "ControlBefore": {"parent": source["native_parent_sha256"], "child": source["native_child_sha256"]},
        "Generated": {"parent": generation["parent_sha256"], "child": generation["child_sha256"]},
        "Reopen": {"parent": native["saved_parent_sha256"], "child": native["saved_child_sha256"]},
        "ControlAfter": {"parent": source["native_parent_sha256"], "child": source["native_child_sha256"]},
    }
    observations = {phase["role"]: phase for phase in raw["phases"]}
    published = {phase["role"]: phase for phase in native["phases"]}
    require(tuple(observations) == tuple(published) == ORDER, "missing or reordered native control or candidate phase")
    identities, numeric_checks = set(), 0
    for role in ORDER:
        phase, pin = observations[role], published[role]
        record = load_bound(packet / "InspectionT01" / role / "Record.json", pin["record_sha256"])
        result = record["result"]
        identity = result["oracle_identity"]
        require(record["passed"] and result["passed"] and pin["passed"] and phase["passed"]
                and record["job"] == {"role": role, "input": inputs[role]}
                and identity == phase["oracle_identity"] and identity["version_matches"]
                and identity["file_version"] == receipt["oracle"]["version"]
                and identity["sha256"] == trial["oracle_sha256"] == receipt["oracle"]["sha256"]
                and (result["open_errors"], result["open_warnings"]) == (0, 0)
                and not result["dialogs"] and not result["controller_diagnostics"]
                and phase["record_sha256"] == pin["record_sha256"]
                and len(record["checks"]) == phase["numeric_checks"] == pin["numeric_checks"],
                "the measured bundle does not belong to a clean native phase")
        identities.add((identity["process_id"], identity["process_creation_filetime"]))
        numeric_checks += phase["numeric_checks"]
    require(len(identities) == raw["distinct_processes"] == 4
            and numeric_checks == native["numeric_checks"] == 333
            and native["parent_save_status"] == native["child_save_status"] == [True, 0, 0]
            and native["parent_feature_rows"] == 27 and native["child_feature_rows"] == 25,
            "clean native edit save and reopen evidence is incomplete")
    for role, relative in (
        ("ControlBefore", "Native/A22CombinedRotated/author"),
        ("Generated", "FrozenGeneratedT01"), ("Reopen", "WorkingT01"),
    ):
        _ = read_bound(packet / relative / PARENT, inputs[role]["parent"])
        _ = read_bound(packet / relative / CHILD, inputs[role]["child"])
    require(build["assembly"]["sha256"] == inputs["Generated"]["parent"]
            and build["child"]["sha256"] == inputs["Generated"]["child"],
            "the exact full files were not supplied to the generated native phase")
    return request, {name: build[name] for name in ("assembly", "child")}


def bind(root):
    sys.path[:0] = [str(root / "src"), str(root), str(HERE.parent)]
    for name in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentComponentValidate",
        "interchange.document.Validation.DocumentGraphValidate",
        "interchange.document.Validation.DocumentMateEntityValidate",
        "interchange.document.Validation.DocumentMateGroupValidate",
        "interchange.document.Validation.DocumentMateValidate",
        "interchange.document.Validation.DocumentMeshValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(name)
    for name in ("utf-8", "utf-8-sig", "utf-16-le", "latin-1", "ascii", "cp1252"):
        lookup(name)


def refuse(operation, text):
    try:
        operation()
    except ValueError as error:
        require(text in str(error), f"unexpected refusal: {error}")
        return
    raise ValueError(f"unexpected acceptance before {text}")


def bad_graph(parent):
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(parent)
    link = ReadNativeLink(archive, 0)
    stream = "Contents/Config-0-MatesList"
    mates = ReadMatesMut(archive.require(stream), link.ResolvedValue)
    mates.RootsValue[0].FieldsValue["f388"] = 1
    encoded, _ = WriteMatesMut(mates.RootsValue, link.ResolvedValue)
    return BuildSldprt(archive.streams | {stream: encoded}, FormatVersion=4)
