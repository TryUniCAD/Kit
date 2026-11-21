import time
from pathlib import Path

import Swapp
from AuthorCurves import Recorder
from FilletSourcePhase import has_exact_identity, save_part
from OracleIdentity import application_identity
from SweepAuthor import SweepAuthor
from SweepModel import PHASES, require
from SweepPacket import digest


def run_native(case, plans, density, phase, original, derivatives, source_hash, record, constants):
    require(phase in PHASES, "unsupported sweep source phase")
    rec = Recorder(record, {"phase": phase, "case": case})
    rec.data.update(schema="kit.sw2026.standard-sweep-source-phase.v1", writer_output_count=0)
    role, _, action = phase.partition("-")
    source = derivatives[role] if action == "reopen" else original
    target = original if phase == "author" else derivatives[role]
    session, complete = None, False
    with Swapp.Dismisser() as monitor:
        try:
            if phase == "author":
                require(not original.exists() and not any(path.exists() for path in derivatives.values()),
                        "sweep source already exists")
            else:
                require(source.is_file() and digest(source) == source_hash, "immutable native sweep input differs")
            session = rec.call("launch isolated SOLIDWORKS .34 COM", Swapp.Sw, visible=phase == "author")
            identity = rec.call("exact native executable identity", application_identity, session.app)
            rec.data["oracle_identity"] = identity
            rec.flush()
            require(has_exact_identity(identity) and session.revision == "34.5.2", "incorrect native executable or build")
            author = SweepAuthor(session.app, rec, Swapp, constants)
            if phase == "author":
                author.author(session, plans["original"], density)
                author.snapshot(plans["original"], density, "authored")
            else:
                author.model, errors, warnings = rec.call("open exact immutable native sweep", session.open, source,
                                                           read_only=action == "reopen")
                rec.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
                rec.flush()
                require(author.model is not None and errors == warnings == 0, "native open failed or warned")
                require(Path(str(author.get(author.model, "GetPathName"))).resolve() == source.resolve(),
                        "native open returned a different source document")
                cold_plan = plans[role] if action == "reopen" else plans["original"]
                require(author.diagnostics() == 0, "fresh native open has diagnostics")
                rec.data["before_explicit_rebuild"] = author.measure_body(cold_plan, "cold open")
                rec.flush()
                author.snapshot(cold_plan, density, "reopened")
                if action == "edit":
                    author.edit(role, plans["original"], plans[role])
                    author.snapshot(plans[role], density, "edited")
            if action != "reopen":
                save_part(session, rec, author, target)
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
    artifact = source if action == "reopen" else target
    rec.data["dialogs"] = monitor.log
    rec.data["source_immutable"] = phase == "author" or (source.is_file() and digest(source) == source_hash)
    if artifact.is_file():
        rec.data.update(native_sha256=digest(artifact), native_bytes=artifact.stat().st_size)
    rec.data["passed"] = bool(complete and rec.data["source_immutable"] and rec.data.get("native_sha256")
                              and not rec.data["first_failure"] and not rec.data["cleanup_errors"]
                              and not rec.data["dialogs"] and not rec.data.get("controller_diagnostics"))
    rec.data["finished_at"] = time.time()
    rec.flush()
    return rec.data["passed"]
