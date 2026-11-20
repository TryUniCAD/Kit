from argparse import ArgumentParser
from pathlib import Path
from time import time
import json
import os
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProbeThroughAutoScope01 import (
    BUILD, DISCLOSED, GUEST, ORACLE, SHARED, TRIAL,
    checked, digest, disclosed, measure, need, publish, wire,
)


PACKET = "SceneLightCounts02"
SCHEMA = "kit.sw2026.disclosed-scene-light-counts.v1"
CASES = {"One": 1, "Two": 2, "Properties": 2}
PHASES = ("Before", *(name + role for name in CASES for role in ("Author", "Reopen")), "After")
PROPERTIES = ((4, 0.375), (3, -73), (8, "frame-λ-21"))
MEMBERS = {
    "GetLightSourceCount": 0,
    "GetLightSourceName": 1,
    "DeleteLightSource": 1,
    "AddLightSourceExtProperty": 2,
    "GetLightSourceExtProperty": 2,
}


def freeze():
    need(os.name != "nt", "freeze disclosed source authorship on the host")
    trial = disclosed(SHARED / DISCLOSED)
    root = SHARED / PACKET
    root.mkdir(mode=0o700, exist_ok=False)
    tools = {}
    for path in (HERE, HERE.with_name("ProbeThroughAutoScope01.py")):
        source = path.read_bytes()
        with (root / path.name).open("xb") as output:
            output.write(source)
        tools[path.name] = digest(source)
    plan = {"schema": SCHEMA, "guest": str(GUEST / PACKET), "phase_order": PHASES,
            "control_trial_sha256": TRIAL, "control_sha256": trial["files_sha256"][trial["control_file"]],
            "tools": tools, "cases": CASES, "properties": PROPERTIES,
            "oracle_sha256": ORACLE, "oracle_build": BUILD}
    return {"freeze_sha256": publish(root / "Freeze.json", plan), "tool_sha256": tools,
            "native_processes_started": 0, "sealed_payloads_read": 0}


def metadata():
    import ThroughAllApiMetadata as api

    api.MEMBERS = {**api.MEMBERS, "IModelDoc2": tuple(dict.fromkeys((
        *api.MEMBERS["IModelDoc2"], *MEMBERS, "GetPathName", "GetActiveConfiguration",
    )))}
    result = api.metadata()
    rows = result["interfaces"]["IModelDoc2"]["members"]
    signatures = {row["names"][0]: len(row["names"]) - 1 for row in rows
                  if row["names"][0] in MEMBERS and row["invoke_kind"] == 1}
    need(signatures == MEMBERS, "registered light API signatures differ")
    return result


def light_names(author):
    count = int(author.get(author.model, "GetLightSourceCount"))
    need(2 <= count <= 4, "the fixture requires an ordinary ambient and directional scene")
    names = [str(author.get(author.model, "GetLightSourceName", index)) for index in range(count)]
    need("ambient" in names[0].casefold()
         and all("direction" in name.casefold() for name in names[1:]),
         "the actual ambient and directional ordering differs")
    return names


def author_lights(author, directionals, with_properties):
    names = light_names(author)
    need(len(names) == 4, "the fresh author requires one ambient and three directionals")
    for index in range(len(names) - 1, directionals, -1):
        author.get(author.model, "DeleteLightSource", index)
    need(light_names(author) == names[:directionals + 1], "the remaining native lights differ")
    if with_properties:
        for expected_index, (value_type, value) in enumerate(PROPERTIES, 1):
            variant = author.sw.VARIANT(value_type, value)
            index = int(author.get(author.model, "AddLightSourceExtProperty", 1, variant))
            need(index == expected_index, "native light property index differs")
    return names


def read_lights(author, directionals, with_properties):
    names = light_names(author)
    need(len(names) == 1 + directionals, "native directional count differs")
    values = [author.get(author.model, "GetLightSourceExtProperty", 1, index)
              for index in range(len(PROPERTIES))] if with_properties else []
    expected = [value for _, value in PROPERTIES] if with_properties else []
    need(values == expected and [type(value) for value in values] == [type(value) for value in expected],
         "native light property values or types differ")
    return {"names": names, "directional_count": directionals, "properties": values}


def read_phase(folder, name):
    path = folder / name / "Record.json"
    need(path.is_file() and not path.is_symlink(), "phase receipt is unavailable")
    result = json.loads(path.read_bytes())
    need(result["job"]["phase"] == name, "phase receipt does not match its directory")
    return result


def candidate(folder, phase, trial_root, trial, api_sha):
    import Swapp
    from AuthorCurves import Recorder
    from InspectSelectedThroughAll import snapshot, ui_tree
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from ThroughAllAuthor import ThroughAllAuthor
    from ThroughAllSourcePlan import disclosed_cases

    is_author = phase.endswith("Author")
    role = phase.removesuffix("Author").removesuffix("Reopen")
    with_properties = role == "Properties"
    stage = folder / phase
    stage.mkdir(exist_ok=False)
    record = Recorder(stage / "Record.json", {"schema": SCHEMA, "phase": phase, "api_sha256": api_sha})
    path = folder / (role + "Author") / (role + "Lights.SLDPRT")
    case_name = "ControlCase.json"
    case = json.loads(checked(trial_root / case_name, trial["files_sha256"][case_name]))
    result = {"passed": False}
    controller = author = None
    saved_sha = None
    with AssemblyLoadMonitor() as monitor:
        try:
            if not is_author:
                saved_sha = read_phase(folder, role + "Author")["result"]["saved_sha256"]
                checked(path, saved_sha)
            record.call("verify the serial native oracle is idle", Swapp.sweep)
            controller = record.call("start the pinned native light observer", Swapp.Sw)
            identity = record.call("verify native executable", application_identity, controller.app)
            need(identity["version_matches"] and identity["file_version"] == BUILD and identity["sha256"] == ORACLE,
                 "the installed version changed")
            result["native_identity"] = identity
            author = ThroughAllAuthor(controller.app, record, Swapp)
            if is_author:
                recipe = disclosed_cases()[0]
                need(recipe["id"] == "D01", "native control author recipe changed")
                author.build(recipe, controller)
                result["initial_scene"] = author_lights(author, CASES[role], with_properties)
            else:
                model, error, warning = record.call("open the exact native part read only", controller.open, path, read_only=True)
                result["open"] = [model is not None, error, warning]
                author.model = model
                need(result["open"] == [True, 0, 0] and Path(author.get(model, "GetPathName")).samefile(path),
                     "fresh open did not select the exact owned part")
            result["scene"] = read_lights(author, CASES[role], with_properties)
            baseline = snapshot(author, case, edited=False, rebuild=False)
            rebuilt = snapshot(author, case, edited=False, rebuild=True)
            result["rebuilt_scene"] = read_lights(author, CASES[role], with_properties)
            need(ui_tree(baseline) == ui_tree(rebuilt) and result["scene"] == result["rebuilt_scene"],
                 "rebuild changed the expected feature tree or observed lighting")
            if is_author:
                need(not path.exists(), "the owned SaveAs destination exists")
                result["save"] = list(record.call("save a fresh native light count source", controller.save_as, author.model, path))
                need(result["save"] == [True, 0, 0] and path.is_file(), "native source SaveAs warned or failed")
                saved_sha = digest(path.read_bytes())
                need(read_lights(author, CASES[role], with_properties) == result["scene"],
                     "native save changed its light definitions")
            result["saved_sha256"] = saved_sha
            result["numeric_checks"] = len(record.data["checks"])
            result["passed"] = bool(result["numeric_checks"] and all(row["passed"] for row in record.data["checks"]))
        except Exception as error:
            record.failure(error)
        finally:
            if controller is not None:
                if author is not None and author.model is not None:
                    record.call("close the owned document without a second save", controller.close_doc, author.model)
                try:
                    controller.close()
                except Exception as error:
                    record.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["source_unchanged"] = bool(saved_sha and path.is_file() and digest(path.read_bytes()) == saved_sha)
    result["dialogs"] = monitor.log
    result["passed"] = bool(result["passed"] and result["source_unchanged"] and not result["dialogs"]
                            and not result.get("controller_diagnostics") and record.data["first_failure"] is None)
    record.data.update(result=result, passed=result["passed"], finished_at=time())
    record.flush()
    return {"phase": phase, "passed": result["passed"], "record_sha256": digest(record.path.read_bytes())}


def summary(folder, pin, api_sha):
    rows = {name: read_phase(folder, name) for name in PHASES if (folder / name / "Record.json").is_file()}
    identities = [row["result"]["native_identity"]["process_creation_filetime"] for row in rows.values()
                  if "native_identity" in row["result"]]
    ordered = tuple(rows.values())
    serial = all(a["finished_at"] <= b["started_at"] for a, b in zip(ordered, ordered[1:]))
    healthy = bool(serial and len(identities) == len(set(identities))
                   and all(name in rows and rows[name]["passed"] for name in ("Before", "After")))
    outcomes = {}
    if healthy:
        for role in CASES:
            names = (role + "Author", role + "Reopen")
            if not all(name in rows and rows[name]["passed"] for name in names):
                continue
            author, cold = (rows[name]["result"] for name in names)
            need(author["saved_sha256"] == cold["saved_sha256"] and author["scene"] == cold["scene"],
                 "actual cold native scene differs")
            outcomes[role] = {"source_sha256": author["saved_sha256"], "scene": cold["scene"],
                              "candidate_numeric_checks": [author["numeric_checks"], cold["numeric_checks"]]}
    value = {"schema": SCHEMA, "freeze_sha256": pin, "api_sha256": api_sha, "healthy_bracket": healthy,
             "serial": serial, "distinct_processes": len(identities), "outcomes": outcomes,
             "phase_status": {name: row["passed"] for name, row in rows.items()},
             "phase_receipts": {name: digest((folder / name / "Record.json").read_bytes()) for name in rows},
             "passed": bool(healthy and set(outcomes) == set(CASES)),
             "heldout_coverage": 0, "production_coverage": 0, "sealed_payloads_read": 0}
    return value | {"result_sha256": publish(folder / "Result.json", value)}


def guest(args):
    need(os.name == "nt", "native light calls require the registered guest")
    root = args.manifest.parent
    plan = json.loads(checked(args.manifest, args.pin))
    need(root == Path(GUEST / PACKET) and HERE == root / HERE.name
         and plan["schema"] == SCHEMA and plan["guest"] == str(GUEST / PACKET)
         and plan["phase_order"] == list(PHASES) and plan["cases"] == CASES
         and plan["properties"] == [list(row) for row in PROPERTIES]
         and plan["control_trial_sha256"] == TRIAL and plan["oracle_sha256"] == ORACLE
         and plan["oracle_build"] == BUILD, "the frozen source plan changed")
    for name in (HERE.name, "ProbeThroughAutoScope01.py"):
        checked(root / name, plan["tools"][name])
    origin = root.with_name(DISCLOSED)
    trial = disclosed(origin)
    need(plan["control_sha256"] == trial["files_sha256"][trial["control_file"]], "exact native control changed")
    sys.path.insert(0, str(origin / "Tools"))
    folder = Path("C:/KitSdkCandidates") / PACKET
    need(folder.resolve() == folder and not folder.is_symlink(), "owned native directory is redirected")
    path = folder / "ApiMetadata.json"
    if args.mode == "metadata":
        result = metadata()
        folder.mkdir(exist_ok=False)
        return {"metadata_sha256": publish(path, {"freeze_sha256": args.pin, "api": result}),
                "native_processes_started": 0}
    raw = path.read_bytes()
    need(json.loads(raw)["freeze_sha256"] == args.pin, "registered metadata does not belong to the frozen plan")
    api_sha = digest(raw)
    if args.mode == "summary":
        return summary(folder, args.pin, api_sha)
    if args.phase in ("Before", "After"):
        return measure(folder, args.phase, origin, trial)
    need(read_phase(folder, "Before")["passed"], "the leading native control did not pass")
    if args.phase.endswith("Reopen"):
        need(read_phase(folder, args.phase.removesuffix("Reopen") + "Author")["passed"],
             "native reopen needs a successful original save")
    return candidate(folder, args.phase, origin, trial, api_sha)


def main():
    parser = ArgumentParser()
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("freeze")
    for mode in ("metadata", "phase", "summary"):
        command = modes.add_parser(mode)
        command.add_argument("manifest", type=Path)
        command.add_argument("pin")
        if mode == "phase":
            command.add_argument("phase", choices=PHASES)
    args = parser.parse_args()
    result = freeze() if args.mode == "freeze" else guest(args)
    sys.stdout.buffer.write(wire(result))
    return int(result.get("passed") is False)


if __name__ == "__main__":
    sys.exit(main())
