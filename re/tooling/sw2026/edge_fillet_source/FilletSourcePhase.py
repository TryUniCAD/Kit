import time
from pathlib import Path

import Swapp
from AuthorCurves import Recorder, write_json
from FilletAuthor import FilletAuthor
from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity

PHASES = ("author", "reopen-edit-save", "edited-reopen")


def has_exact_identity(identity):
    return (identity.get("file_version") == BUILD and identity.get("sha256") == ORACLE
            and identity.get("version_matches") and identity.get("pe_machine") == "0x8664")


def run_control(control, record_path):
    data = {}
    try:
        require(digest(control) == CONTROL, "immutable control changed before opening")
        inspect(control, result=data, checkpoint=lambda: write_json(record_path, data))
    except Exception as error:
        data["exception"] = repr(error)
    data["passed"] = bool(healthy(data) and data.get("sha256") == CONTROL and digest(control) == CONTROL
                          and has_exact_identity(data.get("oracle_identity", {})))
    write_json(record_path, data)
    return data["passed"]


def save_part(session, recorder, author, target):
    require(not target.exists(), "source save would overwrite an existing part")
    saved = recorder.call("save ordinary native part", session.save_as, author.model, target)
    recorder.data["native_save_status"] = list(saved)
    recorder.flush()
    require(saved == (True, 0, 0) and target.is_file() and target.stat().st_size > 0,
            "native save failed or reported diagnostics")
    require(Path(str(author.get(author.model, "GetPathName"))).resolve() == target.resolve(),
            "saved model did not retain the actual requested path")
    records = []
    for suffix in (".x_t", ".step"):
        export = target.with_suffix(suffix)
        require(not export.exists(), "sibling export would overwrite an existing file")
        status = recorder.call("export independent geometry sibling", session.save_as, author.model, export)
        require(status == (True, 0, 0) and export.is_file() and export.stat().st_size > 0,
                f"native {suffix} sibling export failed or warned")
        require(Path(str(author.get(author.model, "GetPathName"))).resolve() == target.resolve(),
                "geometry sibling export unexpectedly changed the actual model path")
        records.append({"name": export.name, "sha256": digest(export), "bytes": export.stat().st_size})
        recorder.data["geometry_siblings"] = list(records)
        recorder.flush()


def run_source(case, phase, paths, record_path, source_hash, constants):
    require(phase in PHASES, "unsupported native source phase")
    initial, derivative = paths
    source = derivative if phase == "edited-reopen" else initial
    target = initial if phase == "author" else derivative
    recorder = Recorder(record_path, {"case": case, "phase": phase})
    recorder.data.update(schema="kit.sw2026.edge-fillet-source-phase.v1", writer_output_count=0)
    session, complete = None, False
    with Swapp.Dismisser() as monitor:
        try:
            if phase == "author":
                require(not initial.exists() and not derivative.exists(), "native source outputs already exist")
            else:
                require(source.is_file() and digest(source) == source_hash, "exact immutable phase input changed")
            session = recorder.call("launch versioned isolated SOLIDWORKS .34 COM", Swapp.Sw)
            identity = recorder.call("measure native process identity", application_identity, session.app)
            recorder.data["oracle_identity"] = identity
            recorder.flush()
            require(has_exact_identity(identity) and session.revision == "34.5.2", "wrong native executable or build")
            author = FilletAuthor(session.app, recorder, constants)
            radius, edited = case["radius_mm"] / 1000, case["edit_radius_mm"] / 1000
            if phase == "author":
                author.author(case, session)
                author.snapshot(case, "authored", radius)
            else:
                author.model, errors, warnings = recorder.call("open exact native source", session.open, source,
                                                               read_only=phase == "edited-reopen")
                recorder.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
                recorder.flush()
                require(author.model is not None and errors == warnings == 0, "phase open failed or reported diagnostics")
                cold = {"bodies": recorder.call("cold solid body count", Swapp.bodies, author.model),
                        "errors": int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))}
                recorder.data["before_explicit_rebuild"] = cold
                recorder.flush()
                require(cold == {"bodies": 1, "errors": 0}, "fresh native open has no solid or has diagnostics")
                author.snapshot(case, "reopened", edited if phase == "edited-reopen" else radius)
                if phase == "reopen-edit-save":
                    author.edit_radius(radius, edited)
                    author.snapshot(case, "edited", edited)
            if phase != "edited-reopen":
                save_part(session, recorder, author, target)
            complete = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                recorder.data["controller_diagnostics"] = session.diagnostics
    recorder.data["dialogs"] = monitor.log
    artifact = source if phase == "edited-reopen" else target
    recorder.data["source_immutable"] = phase == "author" or (source.exists() and digest(source) == source_hash)
    if artifact.is_file():
        recorder.data.update(native_sha256=digest(artifact), native_bytes=artifact.stat().st_size)
    recorder.data["passed"] = bool(complete and recorder.data["source_immutable"]
                                  and recorder.data.get("native_sha256") and not recorder.data["first_failure"]
                                  and not recorder.data["cleanup_errors"] and not recorder.data["dialogs"]
                                  and not recorder.data.get("controller_diagnostics"))
    recorder.data["finished_at"] = time.time()
    recorder.flush()
    return recorder.data["passed"]
