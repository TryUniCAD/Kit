from argparse import ArgumentParser
from itertools import product
from pathlib import Path
import json
import os

from AuthorCurves import digest, require, write_json
from AuthorImportedBody import SOLID
from AuthorPartProperties import TEXT_PROPERTY, manager, read_text
from AuthorRectangleAnchors import CONTROL, ORACLE, control
from ObserveKernelBodyRestore import measure_body
from ObserveLocalImportedPart import phase


GUEST = Path(r"C:\KitBakedLabelOnly01")
TARGET = GUEST / "Candidate" / "Baked01.SLDPRT"
ARMS = ("SourceLabel", "LabelOnly")
TOOLS = {
    "ObserveBakedLabelContrast.py", "ObserveLocalImportedPart.py", "ObserveKernelBodyRestore.py",
    "RunImportedBodySources.py", "AuthorImportedBody.py", "AuthorPartProperties.py",
    "AuthorRectangleAnchors.py", "AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
}


def checked(path, sha):
    require(path.is_file() and not path.is_symlink() and digest(path) == sha, f"unexpected packet file {path.name}")
    return path


def independent_box(bounds):
    axes = tuple(tuple(value / 1000 for value in axis) for axis in bounds)
    x, y, z = (high - low for low, high in axes)
    require(min(x, y, z) > 0, "source box must have positive extents")
    return {"corners_m": tuple(product(*axes)), "edges": 12, "faces": 6,
            "com_m": tuple((low + high) / 2 for low, high in axes), "volume_m3": x * y * z,
            "area_m2": 2 * (x * y + y * z + z * x)}


def observe_shape(observer, body, expected, *, temporary):
    shape = measure_body(observer, body, expected, temporary=temporary)
    part = observer.typed(observer.model, "PartDoc")
    visible, = observer.get(part, "GetBodies2", SOLID, True)
    observer.exact_object(visible, body, "the interpreted solid is the visible body")
    custom = manager(observer, observer.model, "")
    actual = {name: read_text(observer, custom, name) for name in observer.get(custom, "GetNames") or ()}
    require(set(actual) == set(expected["document_text"]), "the native document has different property names")
    for name, value in expected["document_text"].items():
        row = actual[name]
        require(row["type"] == TEXT_PROPERTY and row["raw"] == row["resolved"] == value and not row["linked"],
                "native identity text does not match its independent source property")
    return {**shape, "visible_solids": 1, "document_text": actual}


def measure(packet_path, pin):
    require(os.name == "nt", "run the native contrast from Windows")
    packet = json.loads(checked(packet_path, pin).read_bytes())
    folder = packet_path.parent
    tools = folder / "Tools"
    require(packet["schema"] == "kit.sw2026.baked-label-native.v1" and packet["oracle_sha256"] == ORACLE
            and set(packet["tools"]) == TOOLS and Path(__file__).resolve().parent == tools
            and not GUEST.exists() and not (folder / "Result.json").exists(), "use a fresh pinned native packet")
    for name, sha in packet["tools"].items():
        checked(tools / name, sha)
    prior = json.loads(checked(folder / "Build.json", packet["build_sha256"]).read_bytes())
    source = json.loads(checked(folder / "SourceAudit.json", packet["source_audit_sha256"]).read_bytes())["cases"]
    actual = source["Baked01.FCStd"]
    owner = actual["physical_owners"]
    identity = {"FreeCAD Source UUID": owner["document_uid"], "FreeCAD Object ID": owner["object_id"],
                "FreeCAD Shape SHA-256": actual["source_lock"]["shape_sha256"]}
    labels = {"SourceLabel": owner["label"], "LabelOnly": source["Baked02.FCStd"]["physical_owners"]["label"]}
    require(set(prior["cases"]) == set(ARMS) and len(set(labels.values())) == 2, "follow the disclosed label-only arms")
    for name in ARMS:
        value = prior["cases"][name]
        require(value["document_self"] == str(TARGET) and value["feature_label"] == labels[name]
                and value["document_text"] == identity and value["configuration"] == "Default",
                "candidate bindings differ from the independent source audit")
        checked(folder / f"{name}.SLDPRT", value["part"]["sha256"])
    GUEST.mkdir()
    TARGET.parent.mkdir()
    (GUEST / "RetainedInputs").mkdir()
    (GUEST / "Saved").mkdir()
    seed = checked(folder / "Control.SLDPRT", CONTROL)
    expected = {**independent_box(actual["strict"]["geometry"]["bounds_mm"]), "document_text": identity}
    report = {"schema": "kit.sw2026.baked-label-native-result.v1", "packet_sha256": pin,
              "build_sha256": packet["build_sha256"], "source_audit_sha256": packet["source_audit_sha256"],
              "oracle_file_version": "34.5.2.0604", "oracle_sha256": ORACLE,
              "heldout_cases": 0, "intact_fcstd_conversions": 0, "phases": {}}

    def record(name, action, *args, **kwargs):
        result = action(GUEST, name, *args, **kwargs)
        report["phases"][name] = result
        write_json(folder / "Result.json", report)
        print(json.dumps({"phase": name, "passed": result["passed"], "open": result.get("open"),
                          "cold_failure": result.get("cold_failure"), "failure": result.get("first_failure")}), flush=True)
        return result

    before = record("ControlBefore", control, seed)
    if before["passed"]:
        for name in ARMS:
            case = prior["cases"][name]
            original = checked(folder / f"{name}.SLDPRT", case["part"]["sha256"]).read_bytes()
            saved = GUEST / "Saved" / f"{name}.SLDPRT"
            with TARGET.open("xb") as out:
                out.write(original)
            observed = record(name, phase, TARGET, case["part"]["sha256"], expected, labels[name],
                              save=saved, measure_shape=observe_shape)
            checked(TARGET, case["part"]["sha256"]).rename(GUEST / "RetainedInputs" / f"{name}.SLDPRT")
            if observed["passed"]:
                record(name + "Reopen", phase, saved, observed["saved_sha256"], expected, labels[name],
                       reference=observed["rebuilt"]["persistent_reference"], measure_shape=observe_shape)
    after = record("ControlAfter", control, seed)
    phases = report["phases"]
    identities = {(case["oracle_identity"]["process_id"], case["oracle_identity"]["process_creation_filetime"])
                  for case in phases.values() if case.get("oracle_identity")}
    report["distinct_native_processes"] = len(identities)
    report["controls_healthy"] = before["passed"] and after["passed"] and len(identities) == len(phases)
    report["both_lifecycles_healthy"] = report["controls_healthy"] and all(
        phases.get(name, {}).get("passed") for arm in ARMS for name in (arm, arm + "Reopen")
    )
    if report["both_lifecycles_healthy"]:
        trees = []
        body_states = []
        for arm in ARMS:
            for stage in (arm, arm + "Reopen"):
                for epoch in ("cold", "rebuilt"):
                    values = phases[stage][epoch]
                    trees.append([("<label>" if row[0] == labels[arm] else row[0], *row[1:])
                                  for row in values["tree_signature"]])
                    body_states.append({key: values["shape"][key] for key in
                                        ("vertices", "edges", "faces", "visible_solids", "document_text")})
        report["tree_parity_except_sole_label"] = all(row == trees[0] for row in trees)
        report["body_state_and_identity_text_exact"] = all(row == body_states[0] for row in body_states)
        report["mass_measured_against_same_source"] = True
    report["passed"] = (report["both_lifecycles_healthy"] and report["tree_parity_except_sole_label"]
                        and report["body_state_and_identity_text_exact"])
    write_json(folder / "Result.json", report)
    return int(not report["passed"])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    raise SystemExit(measure(args.packet.resolve(), args.packet_sha256))
