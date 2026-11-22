from pathlib import Path

import Swapp
from AuthorCurves import Recorder
from FilletSourcePhase import has_exact_identity
from OracleIdentity import application_identity
from SweepAuthor import SweepAuthor
from SweepModel import PATH, SECTION, SWEEP, require
from SweepPacket import digest


def run_cold(case, plan, density, path, source_hash, record, constants):
    rec = Recorder(record, {"phase": "candidate-open", "case": case})
    rec.data.update(schema="kit.sw2026.standard-sweep-candidate-phase.v1", original_sha256=source_hash)
    session, complete = None, False
    with Swapp.Dismisser() as monitor:
        try:
            require(path.is_file() and digest(path) == source_hash, "cold candidate input differs")
            session = rec.call("launch isolated SOLIDWORKS .34 COM", Swapp.Sw, visible=False)
            identity = rec.call("exact native executable identity", application_identity, session.app)
            rec.data["oracle_identity"] = identity
            rec.flush()
            require(has_exact_identity(identity) and session.revision == "34.5.2", "wrong native application")
            author = SweepAuthor(session.app, rec, Swapp, constants)
            author.model, errors, warnings = rec.call("open cold generated sweep", session.open, path, read_only=True)
            rec.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
            rec.flush()
            require(author.model is not None and errors == 0
                    and Path(str(author.get(author.model, "GetPathName"))).resolve() == path.resolve(),
                    "native cold open failed or selected a different document")
            try:
                rec.data["cold_diagnostics"] = author.diagnostics()
                rec.data["cold_solid_count"] = rec.call("cold observed solid count", Swapp.bodies, author.model)
                rec.flush()
                rec.data["cold_ordered_tree"] = author.feature_tree(required_names=(SECTION, PATH, SWEEP))
                rec.data["before_explicit_rebuild"] = author.measure_body(plan, "cold open")
                rec.flush()
            except Exception as error:
                rec.failure(error)
            author.snapshot(plan, density, "reopened")
            require(warnings == 0 and rec.data.get("cold_diagnostics") == 0
                    and "before_explicit_rebuild" in rec.data, "unqualified cold open diagnostics or body")
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
    rec.data["source_immutable"] = path.is_file() and digest(path) == source_hash
    if path.is_file():
        rec.data.update(native_sha256=digest(path), native_bytes=path.stat().st_size)
    rec.data["passed"] = bool(complete and rec.data["source_immutable"] and not rec.data["first_failure"]
                              and not rec.data["cleanup_errors"] and not rec.data["dialogs"]
                              and not rec.data.get("controller_diagnostics"))
    rec.flush()
    return rec.data["passed"]
