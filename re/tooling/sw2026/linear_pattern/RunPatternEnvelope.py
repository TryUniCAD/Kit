from argparse import ArgumentParser
from pathlib import Path
import json
import os
import sys
import time

from PatternEnvelopePacket import BUILD, CONTROL, ORACLE, PHASES, require
from PatternEnvelopePacket import checked, digest, verify


def installed(packet):
    import Swapp
    from AuthorLinearPatternSources import libraries
    from ObliqueCylinderApi import metadata

    require(not Swapp.application_pids(), "metadata preflight requires an idle oracle")
    pattern_api = libraries(packet)
    angle_api = metadata()
    require(not Swapp.application_pids(), "metadata preflight started a CAD process")
    return {"pattern": pattern_api, "angle": angle_api, "python": sys.version}


def saved_hash(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size > 0,
            "owned native save is absent or empty")
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": digest(path.read_bytes())}


def inspect_phase(root, phase, spec, api, pristine, edited, initial, derivative):
    import Swapp
    from AuthorCurves import Recorder
    from AuthorPatternEnvelope import PatternEnvelopeAuthor
    from OracleIdentity import application_identity

    record_path = root / phase / "Record.json"
    record_path.parent.mkdir(exist_ok=False)
    rec = Recorder(record_path, {"phase": phase, "cohort": "disclosed", "specification": "envelope"})
    path = pristine if phase != "spacing-reopen" else edited
    target = pristine if phase == "author" else edited if phase == "spacing-edit" else None
    source = None if phase == "author" else derivative if phase == "spacing-reopen" else initial
    immutable, complete, artifact = False, False, None
    session = None
    try:
        require(phase in PHASES and (target is None or not target.exists()), "stage has an existing or unplanned native output")
        if source is not None:
            checked(path, source["sha256"], source["bytes"])
        rec.data["application_pids_before"] = sorted(Swapp.application_pids())
        rec.flush()
        require(not rec.data["application_pids_before"], "candidate phase cannot attach to a running oracle")
        with Swapp.Dismisser() as monitor:
            try:
                session = rec.call("launch isolated versioned COM", Swapp.Sw)
                identity = rec.call("exact native executable", application_identity, session.app)
                rec.data["oracle_identity"] = identity
                rec.flush()
                require(identity["file_version"] == BUILD and identity["version_matches"]
                        and identity["sha256"] == ORACLE and identity["pe_machine"] == "0x8664"
                        and session.revision == "34.5.2", "native oracle build differs")
                author = PatternEnvelopeAuthor(session.app, rec, api, spec)
                if phase == "author":
                    author.build_envelope(session)
                    author.envelope_state("authored", 0)
                else:
                    model, errors, warnings = rec.call(
                        "open the immutable native source", session.open, path,
                        read_only=phase != "spacing-edit",
                    )
                    rec.data["open"] = {"opened": model is not None, "errors": errors, "warnings": warnings}
                    rec.flush()
                    require(model is not None and errors == warnings == 0
                            and Path(str(author.get(model, "GetPathName"))).resolve() == path.resolve(),
                            "actual native source did not open cleanly at its registered path")
                    author.connect(model)
                    if phase == "spacing-edit":
                        author.envelope_state("pre_edit", 0)
                        author.edit(author.case, "spacing")
                        author.envelope_state("edited", 1)
                    else:
                        author.envelope_state("reopened", int(phase == "spacing-reopen"))
                if target is not None:
                    result = rec.call("save owned native derivative", session.save_as, author.model, target)
                    require(result == (True, 0, 0) and
                            Path(str(author.get(author.model, "GetPathName"))).resolve() == target.resolve(),
                            "native save did not finish cleanly at the owned locator")
                    artifact = saved_hash(target)
                    rec.data["save"] = {"ok": result[0], "errors": result[1], "warnings": result[2],
                                        "artifact": artifact}
                    rec.flush()
                complete = True
            except Exception as error:
                rec.failure(error)
            finally:
                if session is not None:
                    try:
                        session.close()
                    except Exception as error:
                        rec.failure(error, cleanup=True)
                    rec.data["controller_diagnostics"] = session.diagnostics
        rec.data["dialogs"] = monitor.log
        if target is not None and artifact is not None:
            require(saved_hash(target) == artifact, "finished artifact differs from the immediate save checkpoint")
        immutable = source is None or saved_hash(path) == source
    except Exception as error:
        rec.failure(error)
    rec.data["application_pids_after"] = sorted(Swapp.application_pids())
    rec.data["source_immutable"] = immutable
    rec.data["artifact"] = artifact if target is not None else source
    rec.data["passed"] = bool(complete and immutable and rec.data["artifact"] and not rec.data["first_failure"]
                              and not rec.data.get("dialogs") and not rec.data.get("controller_diagnostics")
                              and not rec.data["application_pids_after"])
    rec.data["finished_at"] = time.time()
    rec.flush()
    return rec.data, {"phase": phase, "passed": rec.data["passed"], "sha256": digest(record_path.read_bytes())}


def run_native(root, packet, pin_value, manifest, report):
    import Swapp
    from AuthorCurves import write_json
    from AuthorLinearPatternSources import control_phase

    output = root / "DisclosedTrial"
    output.mkdir(exist_ok=False)
    result_path = output / "Result.json"
    spec = json.loads((packet / "Spec.json").read_bytes())
    control = packet / "Control.SLDPRT"
    pristine = output / "DirectionEnvelope.SLDPRT"
    edited = output / "DirectionEnvelopeSpacing.SLDPRT"
    initial, derivative = None, None
    app_ids = []
    result = {"schema": "kit.sw2026.linear-pattern-envelope-native.v1", "packet_sha256": pin_value,
              "research_revision": manifest["research_revision"], "cohort": "disclosed", "native_build": BUILD,
              "oracle_sha256": ORACLE, "controls": {}, "phases": [], "artifacts": [],
              "application_pids_before": sorted(Swapp.application_pids()), "started_at": time.time(),
              "native_lifecycle_passed": False, "writer_output_count": 0, "heldout_sources_accessed": 0}
    write_json(output / "RegisteredApi.json", report)
    result["metadata_sha256"] = digest((output / "RegisteredApi.json").read_bytes())
    write_json(result_path, result)

    def control_side(side):
        key = "Control" + side.title()
        if Swapp.application_pids():
            result["controls"][side] = {"passed": False, "reason": "prior oracle process still running"}
            return
        evidence, identity = control_phase(control, CONTROL, output / (key + ".json"))
        result["controls"][side] = evidence
        if identity is not None:
            app_ids.append(identity)
        write_json(result_path, result)

    try:
        require(not result["application_pids_before"], "oracle is already active")
        control_side("before")
        if result["controls"]["before"]["passed"]:
            for phase in PHASES:
                data, row = inspect_phase(output, phase, spec, report["angle"], pristine, edited, initial, derivative)
                result["phases"].append(row)
                identity = data.get("oracle_identity")
                if identity:
                    app_ids.append(identity["process_creation_filetime"])
                if row["passed"] and phase == "author":
                    initial = data["artifact"]
                elif row["passed"] and phase == "spacing-edit":
                    derivative = data["artifact"]
                result["artifacts"] = [item for item in (initial, derivative) if item]
                write_json(result_path, result)
                if not row["passed"]:
                    break
    except Exception as error:
        result["failure"] = repr(error)
        write_json(result_path, result)
    finally:
        control_side("after")
        result["application_pids_after"] = sorted(Swapp.application_pids())
        result["distinct_processes"] = len(set(app_ids))
        result["process_creation_filetimes"] = app_ids
        result["finished_at"] = time.time()
        try:
            verify(packet, pin_value)
            result["packet_unchanged"] = True
            require(initial and derivative and saved_hash(pristine) == initial
                    and saved_hash(edited) == derivative and initial["sha256"] != derivative["sha256"],
                    "final native source artifacts are incomplete, identical or changed")
            result["artifacts_unchanged"] = True
        except Exception as error:
            result["final_binding_failure"] = repr(error)
        result["native_lifecycle_passed"] = bool(
            all(row["passed"] for row in result["controls"].values())
            and set(result["controls"]) == {"before", "after"}
            and [row["phase"] for row in result["phases"]] == list(PHASES)
            and all(row["passed"] for row in result["phases"])
            and len(app_ids) == len(set(app_ids)) == 6
            and app_ids == sorted(app_ids)
            and not result["application_pids_after"] and not result["application_pids_before"]
            and result.get("packet_unchanged") and result.get("artifacts_unchanged") and "failure" not in result
        )
        write_json(result_path, result)
    print(json.dumps({"native_lifecycle_passed": result["native_lifecycle_passed"],
                      "distinct_processes": result["distinct_processes"],
                      "process_result_sha256": digest(result_path.read_bytes())}))
    return int(not result["native_lifecycle_passed"])


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()
    require(os.name == "nt", "only the root-owned Windows oracle may execute this staged packet")
    packet = Path(__file__).resolve().parents[1]
    manifest = verify(packet, args.pin)
    root = Path(manifest["guest_trial_root"])
    require(root.is_absolute() and (root / "Packet").resolve() == packet,
            "native script is not at its frozen managed locator")
    require(not (root / "DisclosedTrial").exists(), "use a fresh native trial")
    report = installed(packet)
    if args.mode == "verify":
        print(json.dumps({"passed": True, "build": BUILD, "packet_sha256": args.pin,
                          "native_processes_started": 0}))
        return 0
    return run_native(root, packet, args.pin, manifest, report)


if __name__ == "__main__":
    raise SystemExit(main())
