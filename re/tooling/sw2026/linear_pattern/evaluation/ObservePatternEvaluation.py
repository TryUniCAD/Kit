from math import dist
from pathlib import Path

from AuthorCurves import Recorder, require
from AuthorPatternEnvelope import PatternEnvelopeAuthor
from LinearPatternSpecs import rectangle
from ObserveGeneratedLinearPattern import author_spec, measure_geometry, state
from OracleIdentity import application_identity
from PatternEnvelopePacket import BUILD, ORACLE, digest
from PlanPatternEvaluation import DRIVERS, LABELS, match_points
from RunPatternEnvelope import saved_hash
import Swapp


def features(author):
    owners = {}
    for name in LABELS:
        feature = author.get(author.model, "FeatureByName", name)
        require(feature is not None, "an exact authored graph owner is missing")
        owners[name] = feature
    return owners


def observed_parameters(author, owners, reference, path):
    model = reference["modeled_input"]
    values = {"PlateBoss": model["seed"]["plate"]["bounds_m"][1][2],
              "SeedBoss": model["seed"]["seed"]["bounds_m"][1][2],
              "EnvelopeDirection": model["plane"]["angle_rad"]}
    result = {}
    for name, expected in values.items():
        dim = author.typed(author.get(author.model, "Parameter", f"D1@{name}"), "Dimension")
        require(dim is not None and not author.get(dim, "ReadOnly") and author.get(dim, "DrivenState") == 2,
                "owner lost its actual editable D1")
        require(author.get(dim, "FullName").split("@") == ["D1", name, path.stem + ".Part"],
                "D1 does not bind the current native feature and document")
        author.rec.close_number("actual authored D1", author.get(dim, "SystemValue"), expected)
        result[name] = [["D1", name]]
    pattern = model["pattern"]
    returned, _ = author.observe_dimensions(owners["LinearPattern"], pattern["pitch_m"], pattern["count"])
    for role, label in DRIVERS.items():
        require(returned["bindings"][role].split("@") == [label, "LinearPattern", path.stem + ".Part"],
                "pattern display handle does not belong to the current case")
    names = [row["full_name"].split("@") for row in returned["all"]]
    require(all(len(name) == 3 and name[1:] == ["LinearPattern", path.stem + ".Part"] for name in names),
            "pattern exposes an unrelated display dimension")
    result["LinearPattern"] = [name[:2] for name in names]
    return result


def observed_mode(author, feature, seed):
    definition = author.typed(author.get(feature, "GetDefinition"), "LinearPatternFeatureData")
    require(author.get(definition, "AccessSelections", author.model, Swapp.nothing()), "actual pattern scope inaccessible")
    try:
        selected, = list(author.get(definition, "PatternFeatureArray"))
        require(author.persistent(selected, "selected seed")["hex"] == author.persistent(seed, "actual seed")["hex"],
                "pattern scopes onto a different actual seed")
        options = ("FeatureScope", "AutoSelect", "BodyPattern", "GeometryPattern", "VarySketch", "InstancesToVary",
                   "IsDirection2Specified", "D2Spacing", "D2TotalInstances")
        result = {key: author.get(definition, key) for key in options}
        bodies = list(author.get(definition, "FeatureScopeBodies") or ())
        require(bool(result["FeatureScope"]) and not any(bool(result[key]) for key in options[1:-2])
                and float(result["D2Spacing"]) == 0.0 and int(result["D2TotalInstances"]) == 1 and len(bodies) == 1,
                "pattern did not retain its exact single selected stock and sole active direction")
        result["scoped_bodies"] = len(bodies)
        return result
    finally:
        author.get(definition, "ReleaseSelectionAccess")


def enriched_state(author, reference, label, path):
    result = state(author, reference, label)
    owners = features(author)
    dependencies = {name: [str(author.get(parent, "Name")) for parent in author.get(feature, "GetParents") or ()]
                    for name, feature in owners.items()}
    require(all(len(names) == len(set(names)) for names in dependencies.values())
            and dependencies["LinearPattern"] == ["SeedBoss", "EnvelopeDirection"],
            "unexpected authored direct dependency owner or order")
    bounds = author.extreme_bounds()
    match_points(bounds["vertices"], reference["independent_cell_measure"]["vertices_m"])
    result["geometry"]["vertices_m"] = bounds["vertices"]
    result["dependencies"] = dependencies
    result["boss_modes"] = [author.inspect_feature(name, sketch, values["bounds_m"][1][2] * 1000.0, True)
                            for role in ("plate", "seed")
                            for values in [reference["modeled_input"]["seed"][role]]
                            for name, sketch in [(values["feature"], values["sketch"])]]
    result["profiles"] = [author.inspect_profile(name, rectangle(author.case, is_seed))[0]
                          for name, is_seed in (("PlateSketch", False), ("SeedSketch", True))]
    result["pattern_mode"] = observed_mode(author, owners["LinearPattern"], owners["SeedBoss"])
    result["driver_owners"] = observed_parameters(author, owners, reference, path)
    return result


def observe(directory, label, source, identity, original, target, api, *, edit_role=None, destination=None):
    output = directory / f"{label}.json"
    rec = Recorder(output, {"phase": label, "source_sha256": identity["sha256"]})
    result = {"passed": False}
    rec.data["result"] = result
    start_identity = saved_hash(source)
    require(start_identity["sha256"] == identity["sha256"] and (not destination or source != destination),
            "immutable phase source digest or derivative locator differs")
    session = None
    with Swapp.Dismisser() as dialogs:
        try:
            require(not Swapp.application_pids(), "native phase requires an idle oracle")
            session = rec.call("launch isolated versioned COM", Swapp.Sw)
            exact = rec.call("verify executable and lifetime", application_identity, session.app)
            result["identity"] = exact
            require(exact["version_matches"] and exact["file_version"] == BUILD and exact["sha256"] == ORACLE
                    and exact["pe_machine"] == "0x8664" and session.revision == "34.5.2",
                    "unexpected licensed oracle build")
            model, error, warning = rec.call("open exact phase source", session.open, source, read_only=destination is None)
            result["open"] = {"opened": model is not None, "error": error, "warning": warning}
            rec.flush()
            require(model is not None and error == warning == 0, "native phase did not open the exact part cleanly")
            author = PatternEnvelopeAuthor(session.app, rec, api["angle"], author_spec(
                original["modeled_input"], original["independent_cell_measure"], target["modeled_input"]))
            author.connect(model)
            require(Path(author.get(model, "GetPathName")).samefile(source)
                    and bool(author.get(model, "IsOpenedReadOnly")) is (destination is None),
                    "native open locator or access mode differs")
            current = original if destination else target
            result["cold"] = measure_geometry(author, current["independent_cell_measure"], "cold")
            require(author.get(model, "ForceRebuild3", False), "native rebuild did not succeed")
            result["rebuilt"] = enriched_state(author, current, "rebuilt", source)
            if destination:
                require(edit_role in DRIVERS and not destination.exists(), "native edit needs a new derivative")
                author.case["edit_instances"] = target["modeled_input"]["pattern"]["count"]
                author.edit(author.case, edit_role)
                require(rec.data["edit"]["actual_dimension_full_name"].split("@")
                        == [DRIVERS[edit_role], "LinearPattern", source.stem + ".Part"]
                        and author.get(model, "ForceRebuild3", False), "actual isolated driving edit failed")
                result["edited"] = enriched_state(author, target, "edited", source)
                require(result["rebuilt"]["tree"] == result["edited"]["tree"]
                        and result["rebuilt"]["dependencies"] == result["edited"]["dependencies"],
                        "single driver edit altered native ownership")
                require(session.save_as(model, destination) == (True, 0, 0)
                        and Path(author.get(model, "GetPathName")).samefile(destination),
                        "clean native save to the separate local derivative failed")
                result["saved"] = saved_hash(destination)
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if session is not None:
                try:
                    session.close()
                    result["controller_diagnostics"] = session.diagnostics
                except Exception as error:
                    rec.failure(error, cleanup=True)
    result["passed"] = bool(result["passed"] and not dialogs.log and not rec.data["cleanup_errors"]
                            and not result.get("controller_diagnostics") and rec.data["checks"]
                            and all(check["passed"] for check in rec.data["checks"])
                            and not Swapp.application_pids() and saved_hash(source) == start_identity
                            and (not destination or saved_hash(destination) == result.get("saved")))
    result["numeric_checks"] = len(rec.data["checks"])
    rec.data["passed"] = result["passed"]
    rec.flush()
    return result, digest(output.read_bytes())
