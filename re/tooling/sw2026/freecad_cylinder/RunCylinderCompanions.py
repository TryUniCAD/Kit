from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def checked(path, expected):
    raw = path.read_bytes()
    require(not path.is_symlink() and sha256(raw).hexdigest() == expected,
            f"cylinder companion source packet changed: {path.name}")
    return raw


def verify(packet_path, packet_sha):
    root = packet_path.parent.resolve(strict=True)
    packet = json.loads(checked(packet_path, packet_sha))
    require(packet["schema"] == "kit.sw2026.freecad-cylinder-companion-packet.v1"
            and packet["hidden_inputs_read"] == 0 and packet["expected_native_processes"] == 8,
            "use the disclosed two-case cylinder source packet")
    require(Path(__file__).resolve().parent == root / "Tools",
            "source controller must use its immutable packet tools")
    tools = {"AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py", Path(__file__).name}
    require(set(packet["tools"]) == tools, "cylinder source tools differ")
    for name, identity in packet["tools"].items():
        checked(root / "Tools" / name, identity)
    deck = json.loads(checked(root / "Deck.json", packet["deck_sha256"]))
    require(deck["passed"] and deck["oracle_build"] == "34.5.2.0604"
            and deck["authored_native_sources"] == deck["native_processes_started"] == deck["heldout_inputs_read"] == 0
            and tuple(row["case"] for row in deck["cases"]) == ("CylinderA", "CylinderB"),
            "cylinder companion input scope differs")
    checked(root / "Control.SLDPRT", packet["control_sha256"])
    return root, packet, deck


def run(packet_path, packet_sha):
    require(os.name == "nt", "native companion authoring requires the root owned Windows oracle")
    from AuthorCurves import application_pids, author_case, dispatch_job, tool_hashes, write_json
    from InspectFresh import healthy, inspect

    root, packet, deck = verify(packet_path, packet_sha)
    output = root / "Inspection"
    require(not application_pids(), "another SOLIDWORKS process is active")
    output.mkdir(exist_ok=False)
    status = {
        "schema": "kit.sw2026.disclosed-cylinder-companion-oracle.v1",
        "packet_sha256": packet_sha, "passed": False, "controls": {}, "cases": {},
        "hidden_inputs_read": 0, "source_original_admission": False,
        "primitive_lowering_implemented": False, "generative_writer_qualified": False,
    }
    report = output / "Result.json"
    oracle = packet["oracle"]
    timeout = packet["native_phase_timeout_seconds"]
    require(type(timeout) is int and 0 < timeout <= 600, "native phase timeout differs")
    hashes = tool_hashes()
    require(all(packet["tools"][name] == value for name, value in hashes.items()),
            "selected source author tools differ")

    def checkpoint():
        write_json(report, status)

    def control(label):
        require(not application_pids(), "a control requires an empty process inventory")
        control_file = root / "Control.SLDPRT"
        checked(control_file, packet["control_sha256"])
        row = {}
        status["controls"][label] = row
        result = inspect(control_file, result=row, checkpoint=checkpoint)
        checked(control_file, packet["control_sha256"])
        identity = result.get("oracle_identity", {})
        result["passed"] = bool(healthy(result) and identity.get("sha256") == oracle["executable_sha256"]
                                and identity.get("version_matches"))
        checkpoint()
        return result

    before, after = {}, {}
    try:
        before = control("before")
        require(before["passed"], "before control failed")
        for row in deck["cases"]:
            name = row["case"]
            spec = row["native_spec"]
            authored = author_case(output, spec, oracle, timeout, hashes)
            entry = {"plan": spec, "source_freecad_sha256": row["source_sha256"], "native": authored}
            status["cases"][name] = entry
            checkpoint()
            require(authored.get("passed"), "the actual cylinder author or radius edit failed")
            native_path = Path(authored["native_path"])
            native_sha = authored["sha256"]
            depth_case = {**spec, "edit": row["second_independent_edit"]}
            job = {
                "case": depth_case, "oracle": oracle, "phase": "verify", "native_path": str(native_path),
                "tool_hashes": hashes, "source_sha256": native_sha, "dimensions": authored["author"]["dimensions"],
                "requested_relations": authored["author"]["requested_relations"],
            }
            depth = dispatch_job(output / "Depth" / name, job, timeout)
            entry["independent_depth"] = depth
            checkpoint()
            require(depth.get("passed") and depth.get("source_sha256_after") == native_sha,
                    "independent depth edit failed or modified the frozen source")
            checked(native_path, native_sha)
    except Exception as error:
        status["error"] = repr(error)
    finally:
        try:
            after = control("after")
            verify(packet_path, packet_sha)
        except Exception as error:
            status["after_control_error"] = repr(error)
        before_after = [before, after]
        records = [entry for row in status["cases"].values()
                   for entry in (row["native"].get("author"), row["native"].get("verify"), row.get("independent_depth"))
                   if entry is not None]
        identities = [value.get("identity") for value in records] + [r.get("oracle_identity") for r in before_after]
        starts = {(valid.get("process_id"), valid.get("process_creation_filetime"))
                  for valid in identities if valid and valid.get("process_id") and valid.get("process_creation_filetime")}
        status["distinct_native_processes"] = len(starts)
        status["controls_healthy"] = bool(before.get("passed") and after.get("passed")
                                          and before.get("mass") == after.get("mass"))
        status["passed"] = bool(status["controls_healthy"] and len(starts) == 8 and len(records) == 6
                                and all(record.get("passed") for record in records)
                                and "error" not in status and "after_control_error" not in status and not application_pids())
        checkpoint()
    return status


def main():
    parser = ArgumentParser(description="Measure actual native companions for two disclosed FreeCAD cylinders")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.command == "verify":
        verify(args.packet, args.packet_sha256)
        print(json.dumps({"passed": True, "native_processes_started": 0, "hidden_inputs_read": 0}))
        return
    status = run(args.packet, args.packet_sha256)
    print(json.dumps({key: status[key] for key in ("passed", "controls_healthy", "distinct_native_processes", "hidden_inputs_read")}))
    sys.exit(0 if status["passed"] else 1)


if __name__ == "__main__":
    main()
