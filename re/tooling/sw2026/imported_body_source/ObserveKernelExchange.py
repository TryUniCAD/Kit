from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from time import time

from AuthorCurves import Recorder, digest, require
from AuthorImportedBody import ImportedBodyAuthor, SHEET, SOLID
from ObserveKernelBodyRestore import measure_body, run
from RunImportedBodySources import DISCLOSED, oracle_identity


PREFERENCE_GUID = "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}"


def prepare_exchange(observer, controller, path, case):
    if case is None:
        observer.author(controller, DISCLOSED)
        observer.rebuild()
        status = observer.rec.call("export native binary Parasolid control", controller.save_as, observer.model, path)
        require(tuple(status) == (True, 0, 0), "binary Parasolid control export reported diagnostics")
        controller.close_doc(observer.model)
        observer.model = None
        data = path.read_bytes()
    else:
        with path.open("xb") as file:
            file.write(case)
        data = path.read_bytes()
        require(data == case, "binary Parasolid candidate changed when staged")
    require(bool(data), "binary Parasolid exchange control is empty")
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def exchange_body(observer, expected):
    part = observer.typed(observer.model, "PartDoc")
    bodies = tuple(observer.get(part, "GetBodies2", SOLID, False) or ())
    require(len(bodies) == 1 and not observer.get(part, "GetBodies2", SHEET, False),
            "binary Parasolid import does not expose one exclusive solid")
    return measure_body(observer, observer.typed(bodies[0], "Body2"), expected, temporary=False)


def phase(directory, label, expected, candidate, binding):
    import Swapp
    from OracleIdentity import application_identity

    require(binding == "exchange", "exchange probe has a distinct method")
    rec = Recorder(directory / (label + ".json"), {"case": label})
    result, controller, observer = {"passed": False}, None, None
    preference, previous = None, None
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("verify idle oracle", Swapp.sweep)
            controller = rec.call("launch binary Parasolid oracle", Swapp.Sw)
            require(controller.revision == "34.5.2", "unexpected exchange oracle revision")
            result["oracle_identity"] = oracle_identity(rec.call("bind exchange oracle", application_identity, controller.app))
            observer = ImportedBodyAuthor(controller.app, rec, Swapp)
            path = directory / (label + "Payload.x_b")
            result["payload"] = prepare_exchange(observer, controller, path, candidate)
            constants = rec.call("load exact swconst 34", Swapp.wc.gencache.EnsureModule,
                                 PREFERENCE_GUID, 0, 34, 0, bForDemand=False)
            require(constants.MajorVersion == 34 and constants.MinorVersion == 0, "unexpected preference enumeration build")
            preference = int(Swapp.wc.constants.swMultiCAD_Enable3DInterconnect)
            previous = bool(observer.get(controller.app, "GetUserPreferenceToggle", preference))
            rec.data["initial_interconnect_preference"] = {"id": preference, "enabled": previous}
            rec.flush()
            if previous:
                observer.get(controller.app, "SetUserPreferenceToggle", preference, False)
            require(not observer.get(controller.app, "GetUserPreferenceToggle", preference),
                    "ordinary Parasolid translator is not active")
            error = Swapp.byref_long()
            observer.model = observer.get(controller.app, "LoadFile4", str(path), "r", Swapp.nothing(), error)
            result["load_error"] = int(error.value)
            require(observer.model is not None and result["load_error"] == 0, "binary Parasolid exchange import failed")
            result["cold"] = exchange_body(observer, expected)
            observer.rebuild()
            require(int(observer.get(observer.get(observer.model, "Extension"), "GetWhatsWrongCount")) == 0,
                    "binary Parasolid import produced native rebuild diagnostics")
            result["rebuilt"] = exchange_body(observer, expected)
            require(digest(path) == result["payload"]["sha256"], "binary Parasolid input changed during import")
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    if observer is not None and previous is not None:
                        current = bool(observer.get(controller.app, "GetUserPreferenceToggle", preference))
                        if current is not previous:
                            observer.get(controller.app, "SetUserPreferenceToggle", preference, previous)
                        require(bool(observer.get(controller.app, "GetUserPreferenceToggle", preference)) is previous,
                                "3D Interconnect setting was not restored")
                        result["preference_restored"] = True
                    if observer is not None and observer.model is not None:
                        controller.close_doc(observer.model)
                except Exception as error:
                    rec.failure(error, cleanup=True)
                finally:
                    try:
                        controller.close()
                        result["controller_diagnostics"] = controller.diagnostics
                    except Exception as error:
                        rec.failure(error, cleanup=True)
    result["passed"] = bool(result["passed"] and result.get("preference_restored") and not dialogs.log
                            and not result.get("controller_diagnostics") and not rec.data["first_failure"]
                            and not rec.data["cleanup_errors"])
    result["numeric_checks"] = len(rec.data["checks"])
    result["first_failure"] = rec.data["first_failure"]
    rec.data.update(result=result, passed=result["passed"], finished_at=time())
    rec.flush()
    return result | {"record_sha256": digest(rec.path)}


if __name__ == "__main__":
    parser = ArgumentParser(description="Observe ordinary native Parasolid exchange on the pinned SOLIDWORKS build")
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.job.resolve(), args.job_sha256, native_phase=phase,
                         extra_tools=(Path(__file__).name,)))
