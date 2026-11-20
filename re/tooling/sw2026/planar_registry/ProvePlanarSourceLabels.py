from argparse import ArgumentParser
from dataclasses import replace
import json
from pathlib import Path
from subprocess import check_output, run
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent))
from PlanarRegistryBuild import ROOT, bind, file_sha, fingerprint, load, require, write


BASE = "b503656075e6934107884e15fd041705bf5c07f0"
PRIOR_OBSERVATION = "fb68f130ad521ca7473c6f3f239a71a276ccb2318c75586b1eb63de930965f55"
PUBLIC_LOCK = "8f79ed2aa8559b7186f414330b495ce50c4fa3612f69d421bbd7bc83037ca417"
HERE = Path(__file__).resolve()
PROJECTOR = HERE.with_name("PlanarSourceLabels.py")


def checked(path, digest):
    require(path.is_file() and not path.is_symlink(), "expected a regular prior source: " + path.name)
    raw = path.read_bytes()
    require(fingerprint(raw)["sha256"] == digest, "the locked source identity differs: " + path.name)
    return raw


def strict_read(parent, digest):
    tool = ROOT / "re/tooling/sw2026/ReadSdkOrderedNative.py"
    result = run((sys.executable, "-I", "-B", str(tool), "read", "--root", str(ROOT), "--file", str(parent)),
                 capture_output=True, check=False, timeout=90)
    require(result.returncode == 0, result.stderr.decode(errors="replace"))
    row = json.loads(result.stdout)
    require(row["input_sha256"] == digest and row["com_imports"] == [],
            "the strict source reader used another input or imported CAD dependencies")
    return row, fingerprint(result.stdout)["sha256"]


def refusal(operation, args, message):
    try:
        operation(*args)
    except ValueError as error:
        require(str(error) == message, "unexpected refusal: " + repr(error))
        return repr(error)
    raise ValueError("unqualified input was admitted")


def reconstruct(source, source_json, projected, directory):
    from OriginPortableWire import canonical, make_ledger, restore
    from interchange.serialization.EncodeData import ToData

    source_wire, projected_wire = ToData(source), ToData(projected)
    require(canonical(source_wire) == canonical(json.loads(source_json)),
            "the source neutral wire changed during document intake")
    original_child = source_wire["assembly"]["documents"]["$tuple"][0]["document"]
    normalized_child = projected_wire["assembly"]["documents"]["$tuple"][0]["document"]
    parent_ledger = make_ledger(source_wire, projected_wire)
    child_ledger = make_ledger(original_child, normalized_child)
    require(canonical(restore(projected_wire, parent_ledger)) == canonical(source_wire)
            and canonical(restore(normalized_child, child_ledger)) == canonical(original_child),
            "a source owner was lost from the inverse neutral custody")
    retained = write(directory / "SourceNeutralCustody.json", {
        "source_document": source_wire, "parent_inverse": parent_ledger, "child_inverse": child_ledger,
    })
    return {
        "private_custody_sha256": retained,
        "source_wire_sha256": fingerprint(canonical(source_wire))["sha256"],
        "source_child_wire_sha256": fingerprint(canonical(original_child))["sha256"],
        "projected_wire_sha256": fingerprint(canonical(projected_wire))["sha256"],
        "parent_inverse_keys": [row["key"] for row in parent_ledger],
        "child_inverse_keys": [row["key"] for row in child_ledger],
        "complete_source_wire_restored_exactly": True,
        "complete_source_child_wire_restored_exactly": True,
    }


def compare_construction(document, labels, source_display, source_hashes):
    from CheckOriginalPlanarMethod import no_recorded_state
    from ProveSketchLabelIntent import RESOLVED, changed, defaults, evidence, label_rows, payload, predict, send

    child = document.assembly.documents[0].document
    neutral = payload(document, labels)
    no_recorded_state(neutral)
    raw = json.dumps(neutral, sort_keys=True, separators=(",", ":"), allow_nan=False)
    require(not any(digest in raw for digest in source_hashes),
            "the guarded writer request retained a source-native identity")
    output = evidence(send(neutral), send(neutral), neutral, predict(child, labels))
    control_request = payload(document, None)
    no_recorded_state(control_request)
    control_labels = label_rows(child, defaults(child), (False, False))
    control = evidence(send(control_request), send(control_request), control_request, predict(child, control_labels))
    require(output["parent"] == control["parent"]
            and changed(control["child"]["streams"], output["child"]["streams"]) == [RESOLVED]
            and {name: row["owner"] for name, row in output["actual"].items()}
            == {name: row["owner"] for name, row in control["actual"].items()},
            "source labels changed the parent bundle, an unrelated child stream or owner identity")
    number_changes = {}
    from RectanglePresentation import differences

    for name, dimension in (("D1", "width"), ("D2", "height")):
        supplied, stored = source_display[dimension], output["actual"][name]
        require(stored["intent"] == {"text_point_m": supplied["text_m"],
                                     "route_centerline": supplied["centerline_route"]},
                "the generated label lost its source-derived semantic values")
        source_witness = {key: supplied[key] for key in
                          ("along_fraction", "away_m", "along_axis", "away_axis", "start_m", "end_m")}
        generated_witness = {key: stored["witness"][key] for key in source_witness}
        require(not differences(source_witness, generated_witness),
                "the newly computed witnesses differ materially from the bounded source")
        number_changes[name] = differences(source_witness, generated_witness, absolute=0)
    return {"generated": output, "default_control": control,
            "child_changed_streams": [RESOLVED], "parent_exact": True,
            "source_label_xyz_and_routes_exact": True,
            "source_and_generated_witness_arithmetic_differences": number_changes}


def initial_gate(source):
    from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import CheckAsmShape

    child = source.assembly.documents[0].document
    group_rows = [row.id for row in source.feature_timeline
                  if getattr(row.definition, "object_data", {}).get("native_class") == "moMateGroup_c"]
    require(len(group_rows) == 1 and not source.assembly.mate_groups,
            "the source assembly group ownership differs from the previously evaluated profile")
    return {
        "refusal": refusal(CheckAsmShape, (source,), "assembly root contains unprojected model content"),
        "actual_native_root_rows": len(source.feature_timeline),
        "actual_source_child_rows": len(child.feature_timeline),
        "diagnostic_codes": [row.code for row in source.diagnostics],
        "actual_mates_feature_ids": group_rows, "neutral_mate_group_count": len(source.assembly.mate_groups),
        "root_metadata_keys": sorted(source.metadata), "child_metadata_keys": sorted(child.metadata),
        "root_source_extension_keys": sorted(source.source.attributes),
        "child_source_extension_keys": sorted(child.source.attributes),
        "child_literal_property_count": len(child.metadata["custom_properties"]),
        "child_summary_item_count": len(child.metadata["document_summary"]),
    }


def crossed_relation(source):
    child = source.assembly.documents[0].document
    sketch, = child.sketches
    width, height = [row for row in sketch.constraints if row.parameter_id]
    crossed = replace(width, attributes={**width.attributes,
                                        "native_handle_index": height.attributes["native_handle_index"]})
    return replace(child, sketches=(replace(sketch, constraints=tuple(
        crossed if row is width else row for row in sketch.constraints)),))


def prove(packet, output):
    bind(ROOT)
    from interchange import CadDocument
    from PlanarPriorAdmission import PRIOR, source_intent
    from PlanarSourceLabels import bridge, project_labels

    modifications = check_output(("git", "diff", "--name-only", BASE, "--", "src", "tests", "re/tooling/sw2026"),
                                 cwd=ROOT, text=True).splitlines()
    require(set(modifications) <= {path.relative_to(ROOT).as_posix() for path in (PROJECTOR, HERE)},
            "prior source bridge requires an unchanged pinned SDK and guarded builder")
    previous = load(ROOT / "re/solidworks/measurements/2026/SdkPlanarPriorSourceAdmission01.json", PRIOR_OBSERVATION)
    lock = load(ROOT / "re/solidworks/v2026/heldout/AssemblyPlanarMateSourceLock01.json", PUBLIC_LOCK)
    private_lock = load(packet / "SourceLock.json", lock["private_source_lock_sha256"])
    known = {row["name"]: row for row in lock["cases"] if row["name"] in PRIOR}
    private = {row["name"]: row for row in private_lock["cases"] if row["name"] in PRIOR}
    require(not output.exists() and not output.is_relative_to(ROOT) and not output.is_relative_to(packet),
            "choose an unused private output outside the checkout and locked packet")
    output.mkdir()
    cases, controls, custody, process_ids = {}, {}, [], []
    for name, (parent_hash, child_hash, _, _) in PRIOR.items():
        slot = name[:3]
        prior = previous["cases"][slot]
        observed = prior["exact_source_display"]
        source = packet / name / "author"
        parent, child, record = source / (name + ".SLDASM"), source / "CohortChild.SLDPRT", source / "Record.json"
        author_hash = prior["authority"]["author_record_sha256"]
        require(known[name]["record_sha256"] == private[name]["record_sha256"]
                and known[name]["record_sha256"][0] == author_hash
                and known[name]["native_sha256"] == private[name]["native_sha256"] == parent_hash
                and known[name]["synchronized_child"]["native_sha256"]
                == private[name]["synchronized_child"]["native_sha256"] == child_hash,
                "prior observations and original custody refer to different sources")
        checked(parent, parent_hash)
        child_bytes = checked(child, child_hash)
        author = json.loads(checked(record, author_hash))["job"]
        require(author["phase"] == "author" and author["case"]["name"] == name, "locked author case differs")
        read, stdout = strict_read(parent, parent_hash)
        original = CadDocument.from_json(read["document_json"])
        document, labels, owners = bridge(original, author["case"], child_bytes, observed)
        directory = output / slot
        directory.mkdir()
        inverse = reconstruct(original, read["document_json"], document, directory)
        build = compare_construction(document, labels, observed, (parent_hash, child_hash))
        direct_gate = initial_gate(original)
        projected_child = document.assembly.documents[0].document
        owner_refusal = refusal(
            project_labels, (crossed_relation(original), child_bytes, projected_child, observed),
            "native rectangle display does not match the strict source relation owner",
        )
        process_ids.append(read["worker_pid"])
        for variant in ("generated", "default_control"):
            process_ids.extend(build[variant]["worker_pids"])
        cases[slot] = {
            "original_sha256": {"parent": parent_hash, "child": child_hash, "author": author_hash},
            "strict_reader_stdout_sha256": stdout, "strict_reader_pid": read["worker_pid"],
            "closed_source_gate": direct_gate, "neutral_metadata_custody": inverse,
            "source_label_owners": owners, "neutral_labels": labels, "guarded_label_construction": build,
            "crossed_source_owner_refusal": owner_refusal,
        }
        controls[slot] = original, author["case"], child_bytes
        custody.extend(((parent, parent_hash), (child, child_hash), (record, author_hash)))
    original, author_case, _ = controls["A20"]
    cross = refusal(source_intent, (original, author_case, controls["A21"][2]),
                    "use the exact prior native source custody identities")
    for path, digest in custody:
        checked(path, digest)
    load(packet / "SourceLock.json", lock["private_source_lock_sha256"])
    require(len(set(process_ids)) == len(process_ids) == 10, "the read and two construction repeats must be independent")
    require(not any(name == "Swapp" or name == "pythoncom" or name.startswith("win32com") for name in sys.modules),
            "the label source supervisor imported a CAD runtime")
    manifest_paths = (
        HERE, PROJECTOR, HERE.with_name("PlanarPriorAdmission.py"), HERE.with_name("RectanglePresentation.py"),
        HERE.with_name("SketchLabelIntent.py"), HERE.with_name("ProveSketchLabelIntent.py"),
        ROOT / "re/tooling/sw2026/OriginPortableWire.py", ROOT / "re/tooling/sw2026/ReadSdkOrderedNative.py",
        ROOT / "re/tooling/sw2026/CheckOriginalPlanarMethod.py",
    )
    result = {
        "schema": "kit.sw2026.prior-planar-source-label-bridge.v1", "base_revision": BASE,
        "base_sdk_tree": check_output(("git", "rev-parse", BASE + ":src"), cwd=ROOT, text=True).strip(),
        "source_tool_sha256": {path.relative_to(ROOT).as_posix(): file_sha(path) for path in manifest_paths},
        "interpreter_sha256": file_sha(Path(sys.executable)), "interpreter": sys.version,
        "prior_observation_sha256": PRIOR_OBSERVATION, "original_public_lock_sha256": PUBLIC_LOCK,
        "original_source_lock_sha256": lock["private_source_lock_sha256"],
        "passed": True, "cases": cases, "crossed_child_refusal": cross,
        "strict_source_readers": 2, "guarded_constructor_processes": 8,
        "linked_child_stream_round_trips": 16, "runtime_constructor_reads": 0,
        "source_identities_preserved": True, "label_projection_passed": True,
        "recorded_source_payload_forwarded": False,
        "whole_source_admission": False, "native_artifacts_published": 0,
        "native_processes": 0, "native_acceptance": False, "new_heldout_credit": 0,
    }
    sha = write(output / "Result.json", result)
    return {"passed": True, "result_sha256": sha, "label_projection_count": len(cases),
            "whole_source_admission": False, "native_artifacts_published": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("--source-packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = prove(args.source_packet.resolve(strict=True), args.output.resolve())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
