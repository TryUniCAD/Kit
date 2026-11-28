from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import struct
import sys
import time

from AuthorCurves import Recorder, digest, require, write_json
from AuthorRectangleAnchors import (
    BOSS,
    PARAMETERS,
    SKETCH,
    RectangleAuthor,
    rectangle_points,
)

SCHEMA = "kit.sw2026.equation-source-protocol.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
METADATA = "60db6487419215724e9f48f7f17ae1f5aa373e6cb39a868dda02c31658f7f78c"
PHASES = ("ControlBefore", "Author", "ReopenOriginal", "ReopenEdited", "ControlAfter")
SLOTS = {
    "D01": "global_width",
    "D02": "width_depth",
    "Slot01": "global_width",
    "Slot02": "width_depth",
}


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def hash_value(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(value))


def check_case(case, slot):
    require(
        set(case)
        == {
            "id",
            "family",
            "width_mm",
            "height_mm",
            "depth_mm",
            "edit_width_mm",
            "global_name",
            "divisor",
        },
        "unexpected source intent fields",
    )
    require(
        case["id"] == slot and case["family"] == SLOTS[slot],
        "equation family or source slot differs",
    )
    require(
        case["global_name"].isascii() and case["global_name"].isidentifier(),
        "global variable requires an explicit simple identifier",
    )
    require(
        all(
            type(case[name]) in (int, float)
            and math.isfinite(case[name])
            and 3 < case[name] < 100
            for name in ("width_mm", "height_mm", "depth_mm", "edit_width_mm")
        ),
        "source length outside the preregistered domain",
    )
    require(
        case["width_mm"] != case["edit_width_mm"] and case["divisor"] == 2,
        "source edit or fixed relation grammar differs",
    )
    if case["family"] == "width_depth":
        require(
            case["depth_mm"] == case["width_mm"] / case["divisor"],
            "source pad depth is stale against the actual width relation",
        )


def expected(case, edited=False):
    width = case["edit_width_mm"] if edited else case["width_mm"]
    depth = (
        width / case["divisor"] if case["family"] == "width_depth" else case["depth_mm"]
    )
    width, height, depth = width / 1000, case["height_mm"] / 1000, depth / 1000
    return {
        "dimensions_m": dict(zip(PARAMETERS, (width, height, depth), strict=True)),
        "volume_m3": width * height * depth,
        "area_m2": 2 * (width * height + width * depth + height * depth),
        "center_m": [width / 2, height / 2, depth / 2],
        "corners_m": [
            list(value) for value in rectangle_points("corner", width, height)
        ],
        "body_count": 1,
        "configuration_count": 1,
    }


def number(value):
    return format(value, ".12g")


def equation_rows(case, edited=False):
    if case["family"] == "global_width":
        width = case["edit_width_mm"] if edited else case["width_mm"]
        return [
            f'"{case["global_name"]}" = {number(width)} mm',
            f'"{PARAMETERS[0]}" = "{case["global_name"]}"',
        ]
    return [f'"{PARAMETERS[2]}" = "{PARAMETERS[0]}" / {case["divisor"]}']


def read_job(path, sha):
    require(digest(path) == sha, "the frozen equation protocol changed")
    job = json.loads(path.read_bytes())
    require(
        job["schema"] == SCHEMA
        and job["writer_output_count"] == 0
        and job["native_acceptance"] is False,
        "the source-only equation scope differs",
    )
    require(
        Path(__file__).resolve().parent == path.resolve().parent / "Tools",
        "use the complete frozen equation source tools",
    )
    for relative, wanted in job["files_sha256"].items():
        require(
            digest(path.parent / relative) == wanted,
            "the frozen equation input or tool changed",
        )
    require(
        job["api_metadata_sha256"] == METADATA
        and digest(path.parent / "ApiMetadata01.json") == METADATA,
        "the registered equation API metadata changed",
    )
    require(
        job["oracle_sha256"] == ORACLE and set(job["slots"]) == set(SLOTS),
        "the oracle or declared cohort differs",
    )
    for case in job["disclosed_cases"]:
        check_case(case, case["id"])
    return job


def guest_only(job):
    require(
        os.name == "nt",
        "native equation phases and sealed intent generation run only inside the guest",
    )
    runtime = job["guest_runtime"]
    require(
        sys.version_info[:3] == tuple(runtime["version"])
        and struct.calcsize("P") * 8 == runtime["pointer_bits"]
        and Path(sys.executable).samefile(runtime["executable"]),
        "the exact guest interpreter differs",
    )


def case_root(path, job, slot):
    if slot.startswith("Slot"):
        return Path(job["guest_private_root"]) / slot
    return path.parent / "Disclosed" / slot


def load_case(path, job, slot):
    require(slot in SLOTS, "an undeclared equation source slot was requested")
    directory = case_root(path, job, slot)
    case = json.loads((directory / "Intent.json").read_bytes())
    check_case(case, slot)
    seal = json.loads((directory / "IntentSeal.json").read_bytes())
    require(
        seal["intent_sha256"] == digest(directory / "Intent.json")
        and seal["prediction_sha256"] == digest(directory / "Prediction.json"),
        "sealed intent or independent prediction changed",
    )
    require(
        json.loads((directory / "Prediction.json").read_bytes())
        == {"Original": expected(case), "Edited": expected(case, True)},
        "the frozen source prediction differs from its analytic definition",
    )
    return directory, case, seal


def publish_progress(path, slot, phase, value):
    write_new(path.parent / "Progress" / slot / phase / "Record.json", value)


def seal_intents(path, sha, slot):
    job = read_job(path, sha)
    guest_only(job)
    require(slot in SLOTS, "an undeclared equation source slot was requested")
    directory = case_root(path, job, slot)
    require(not directory.exists(), "source intent root must be unused")
    if slot.startswith("Slot"):
        sampler = secrets.SystemRandom()
        width = sampler.randrange(22001, 61000) / 1000
        edited = sampler.randrange(22001, 61000) / 1000
        while abs(width - edited) < 4:
            edited = sampler.randrange(22001, 61000) / 1000
        case = {
            "id": slot,
            "family": SLOTS[slot],
            "width_mm": width,
            "height_mm": sampler.randrange(10001, 29000) / 1000,
            "depth_mm": sampler.randrange(7001, 19000) / 1000,
            "edit_width_mm": edited,
            "global_name": "source_width_" + secrets.token_hex(4),
            "divisor": 2,
        }
        if case["family"] == "width_depth":
            case["depth_mm"] = width / 2
    else:
        (case,) = [value for value in job["disclosed_cases"] if value["id"] == slot]
    check_case(case, slot)
    write_new(directory / "Intent.json", case)
    write_new(
        directory / "Prediction.json",
        {"Original": expected(case), "Edited": expected(case, True)},
    )
    seal = {
        "schema": "kit.sw2026.equation-intent-seal.v1",
        "slot": slot,
        "protocol_sha256": sha,
        "intent_sha256": digest(directory / "Intent.json"),
        "prediction_sha256": digest(directory / "Prediction.json"),
        "sealed": slot.startswith("Slot"),
        "native_processes_started": 0,
        "writer_output_count": 0,
        "created_at": time.time(),
    }
    write_new(directory / "IntentSeal.json", seal)
    publish_progress(path, slot, "IntentSeal", seal)
    return seal


class EquationAuthor(RectangleAuthor):
    def __init__(self, application, recorder, modules, metadata):
        super().__init__(application, recorder, modules)
        self.metadata = metadata["interfaces"]["IEquationMgr"]["members"]

    def eq(self, manager, name, kind=2, *values):
        (row,) = [
            value
            for value in self.metadata
            if value["names"][0] == name and value["invoke_kind"] == kind
        ]
        require(
            len(row["arguments"]) == len(values),
            "the indexed equation argument count differs from registered metadata",
        )
        result_type = tuple(row["return_type"][:2])
        arguments = tuple(tuple(value[:2]) for value in row["arguments"])
        return self.rec.call(
            "IEquationMgr." + name,
            manager._oleobj_.InvokeTypes,
            row["member_id"],
            0,
            kind,
            result_type,
            arguments,
            *values,
            parameters={
                "member_id": row["member_id"],
                "invoke_kind": kind,
                "return_type": result_type,
                "argument_types": arguments,
                "values": list(values),
                "binding": "registered release-34.0 descriptor",
            },
        )

    def manager(self):
        result = self.get(self.model, "GetEquationMgr")
        require(result is not None, "the actual model has no equation manager")
        return self.typed(result, "IEquationMgr")

    def add_equations(self, case):
        manager = self.manager()
        require(
            self.eq(manager, "GetCount", 1) == 0,
            "new part unexpectedly already owns equations",
        )
        for index, text in enumerate(equation_rows(case)):
            result = self.eq(manager, "Add2", 1, index, text, False)
            require(
                result == index,
                "single-configuration Add2 did not publish the requested row",
            )
        self.rec.data["evaluate_all_return_ungraded"] = self.eq(
            manager, "EvaluateAll", 1
        )
        self.rec.flush()

    def read_equations(self, case, edited):
        manager = self.manager()
        requested = equation_rows(case, edited)
        require(
            self.eq(manager, "GetCount", 1) == len(requested),
            "the actual equation count differs from its declared relation graph",
        )
        rows = []
        for index, text in enumerate(requested):
            actual = str(self.eq(manager, "Equation", 2, index))
            state = int(self.eq(manager, "Status"))
            value = float(self.eq(manager, "Value", 2, index))
            value_state = int(self.eq(manager, "Status"))
            global_variable = bool(self.eq(manager, "GlobalVariable", 2, index))
            disabled = bool(self.eq(manager, "Disabled", 2, index))
            row = {
                "index": index,
                "text": actual,
                "equation_status": state,
                "value": value,
                "value_status": value_state,
                "value_units": "unqualified native raw value; acceptance uses IDimension.SystemValue in SI",
                "global_variable": global_variable,
                "disabled": disabled,
            }
            rows.append(row)
            self.rec.data["latest_equation_rows"] = rows
            self.rec.flush()
            require(
                "".join(actual.split()) == "".join(text.split()),
                "the equation text differs from the independent authored row",
            )
            require(
                global_variable == (case["family"] == "global_width" and index == 0)
                and not disabled,
                "equation global ownership or enabled state differs",
            )
        require(
            not self.eq(manager, "LinkToFile") and not self.eq(manager, "FilePath"),
            "the source relation unexpectedly depends on an external equation file",
        )
        return rows

    def source_snapshot(self, case, edited):
        require(
            self.get(self.model, "ForceRebuild3", False),
            "the equation-driven source failed to rebuild",
        )
        require(
            self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount") == 0,
            "the equation-driven source has rebuild diagnostics",
        )
        want = expected(case, edited)
        part = self.typed(self.model, "PartDoc")
        feature = self.get(part, "FeatureByName", SKETCH)
        require(feature is not None, "the actual equation sketch owner is missing")
        self.sketch = self.get(feature, "GetSpecificFeature2")
        require(self.sketch is not None, "the actual equation sketch is unavailable")
        dimensions = {}
        for name, target in want["dimensions_m"].items():
            dimension = self.get(self.model, "Parameter", name)
            require(
                dimension is not None,
                "an equation dimension has no actual parameter owner",
            )
            full_name = str(self.get(dimension, "FullName"))
            require(
                full_name.split("@")[:2] == name.split("@"),
                "dimension FullName selects a different feature owner",
            )
            value = float(self.get(dimension, "SystemValue"))
            self.rec.close_number(name, value, target)
            dimensions[name] = {
                "full_name": full_name,
                "system_value_m": value,
                "driven_state": int(self.get(dimension, "DrivenState")),
                "read_only": bool(self.get(dimension, "ReadOnly")),
            }
        self.rec.close_number(
            "fully constrained equation sketch",
            self.get(self.sketch, "GetConstrainedStatus"),
            3,
            absolute=0,
        )
        geometry = self.geometry()
        require(
            len(geometry) == 4
            and all(
                row["kind"] == "line" and not row["construction"] for row in geometry
            ),
            "the source sketch no longer has exactly four ordinary lines",
        )
        corners = want["corners_m"]
        remaining = list(zip(corners, corners[1:] + corners[:1], strict=True))
        for row in geometry:
            matches = [
                (index, pair)
                for index, pair in enumerate(remaining)
                if any(
                    all(
                        abs(actual - target) < 1e-10
                        for observed, point in zip(
                            (row["start"], row["end"]), oriented, strict=True
                        )
                        for actual, target in zip(observed, point, strict=True)
                    )
                    for oriented in (pair, pair[::-1])
                )
            ]
            require(
                len(matches) == 1,
                "source line has no unique analytically predicted rectangle edge",
            )
            remaining.pop(matches[0][0])
        bodies = list(self.get(part, "GetBodies2", 0, False) or ())
        require(len(bodies) == 1, "the equation source needs one real solid")
        mass = self.rec.call(
            "measure equation-driven real solid", self.sw.mass, self.model
        )
        require(
            mass is not None and "error" not in mass,
            "source mass properties are unavailable",
        )
        self.rec.close_number(
            "equation solid volume", mass["volume"], want["volume_m3"], absolute=1e-16
        )
        self.rec.close_number(
            "equation solid area", mass["area"], want["area_m2"], absolute=1e-14
        )
        for index, target in enumerate(want["center_m"]):
            self.rec.close_number(
                "equation solid centroid " + str(index), mass["com"][index], target
            )
        configurations = list(self.get(self.model, "GetConfigurationNames") or ())
        require(
            len(configurations) == 1,
            "this Add2 source protocol admits one real configuration only",
        )
        tree = self.feature_tree(required_names=(SKETCH, BOSS))
        require(
            sum(row["type"] == "EqnFolder" for row in tree) == 1,
            "the native feature tree has no unique equation folder",
        )
        return {
            "equations": self.read_equations(case, edited),
            "dimensions": dimensions,
            "geometry": geometry,
            "relations": self.relation_graph(),
            "tree": tree,
            "mass_properties": mass,
            "body_count": len(bodies),
            "configuration_names": configurations,
            "update_stamp": int(self.get(self.model, "GetUpdateStamp")),
        }

    def edit_source(self, case):
        if case["family"] == "global_width":
            manager = self.manager()
            self.eq(manager, "Equation", 4, 0, equation_rows(case, True)[0])
        else:
            dimension = self.get(self.model, "Parameter", PARAMETERS[0])
            require(
                self.get(dimension, "DrivenState") == 2
                and not self.get(dimension, "ReadOnly"),
                "upstream width is no longer an editable driver",
            )
            self.edit(PARAMETERS[0], case["edit_width_mm"] / 1000)
        self.rec.data["evaluate_all_after_edit_ungraded"] = self.eq(
            self.manager(), "EvaluateAll", 1
        )
        self.rec.flush()


class PromptLease:
    def __init__(self, author, path):
        self.author, self.path = author, path
        self.value = {
            "schema": "kit.sw2026.equation-dimension-prompt-lease.v1",
            "protocol_sha256": author.rec.data["job"]["protocol_sha256"],
            "oracle_identity": author.rec.data["oracle_identity"],
            "preference_enum": 10,
            "original": None,
            "restore_required": False,
            "restored": False,
            "document_mutations": "declared vendor source authoring only",
        }

    def enter(self):
        self.value["original"] = bool(
            self.author.get(self.author.app, "GetUserPreferenceToggle", 10)
        )
        self.value["restore_required"] = True
        write_json(self.path, self.value)
        self.author.get(self.author.app, "SetUserPreferenceToggle", 10, False)
        require(
            not self.author.get(self.author.app, "GetUserPreferenceToggle", 10),
            "the dimension prompt lease did not apply",
        )

    def restore(self):
        if self.value["restore_required"]:
            original = self.value["original"]
            self.author.get(self.author.app, "SetUserPreferenceToggle", 10, original)
            require(
                bool(self.author.get(self.author.app, "GetUserPreferenceToggle", 10))
                == original,
                "the actual original dimension-prompt preference was not restored",
            )
            self.value["restored"] = True
            self.value["restore_required"] = False
            write_json(self.path, self.value)


def same_structure(actual, prior):
    for key in ("tree", "relations", "configuration_names"):
        require(
            actual[key] == prior[key],
            "source equation " + key + " changed across the saved lifecycle",
        )


def control_snapshot(author, job):
    want = job["control_prediction"]
    require(
        author.get(author.model, "ForceRebuild3", False)
        and author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount")
        == 0,
        "pristine source control cannot rebuild cleanly",
    )
    bodies = list(
        author.get(author.typed(author.model, "PartDoc"), "GetBodies2", 0, True) or ()
    )
    require(len(bodies) == 1, "pristine source control has no unique visible solid")
    mass = author.rec.call(
        "measure pristine source control", author.sw.mass, author.model
    )
    require(
        mass is not None and "error" not in mass, "pristine control mass is unavailable"
    )
    for key in ("volume", "area"):
        author.rec.close_number(
            "pristine control " + key, mass[key], want[key], absolute=1e-16
        )
    for index, value in enumerate(want["com"]):
        author.rec.close_number(
            "pristine control centroid " + str(index), mass["com"][index], value
        )
    dimensions = {}
    for name, value in job["control_dimensions_m"].items():
        dimension = author.get(author.model, "Parameter", name)
        require(dimension is not None, "pristine control driving owner is missing")
        dimensions[name] = float(author.get(dimension, "SystemValue"))
        author.rec.close_number(name, dimensions[name], value)
    tree = author.feature_tree(required_names=("CurveSketch", "CurveBoss"))
    require(
        [[row["name"], row["type"], row["parent"]] for row in tree]
        == job["control_tree"],
        "pristine native control tree differs",
    )
    return {
        "mass_properties": mass,
        "dimensions_m": dimensions,
        "tree": tree,
        "body_count": 1,
    }


def phase(path, sha, slot, name):
    job = read_job(path, sha)
    guest_only(job)
    require(name in PHASES, "undeclared source phase")
    directory, case, seal = load_case(path, job, slot)
    out = directory / "Inspection" / name
    out.mkdir(parents=True, exist_ok=False)
    from OracleIdentity import application_identity
    import Swapp

    rec = Recorder(
        out / "Record.json",
        {
            "slot": slot,
            "phase": name,
            "intent_sha256": seal["intent_sha256"],
            "protocol_sha256": sha,
        },
    )
    result = {
        "passed": False,
        "source_only": True,
        "writer_output_count": 0,
        "slot": slot,
        "phase": name,
        "files": {},
        "observed": {},
        "intent_sha256": seal["intent_sha256"],
        "prediction_sha256": seal["prediction_sha256"],
    }
    controller, author, lease = None, None, None
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("verify exclusively idle native oracle", Swapp.sweep)
            controller = rec.call("start exact source oracle", Swapp.Sw)
            identity = rec.call(
                "verify exact native source identity",
                application_identity,
                controller.app,
            )
            require(
                identity["sha256"] == ORACLE
                and identity["version_matches"]
                and controller.revision == "34.5.2",
                "the native source build differs",
            )
            result["oracle_identity"] = identity
            rec.data["oracle_identity"] = identity
            rec.flush()
            metadata = json.loads((path.parent / "ApiMetadata01.json").read_bytes())
            author = EquationAuthor(controller.app, rec, Swapp, metadata)
            if name.startswith("Control"):
                source = path.parent / "Control.SLDPRT"
                before = digest(source)
                model, error, warning = rec.call(
                    "open pristine equation source control",
                    controller.open,
                    source,
                    read_only=True,
                )
                require(
                    model is not None
                    and error == warning == 0
                    and Path(author.get(model, "GetPathName")).samefile(source),
                    "the pristine source control failed, warned or selected another file",
                )
                author.model = model
                result["observed"]["Control"] = control_snapshot(author, job)
                require(
                    digest(source) == before == job["files_sha256"]["Control.SLDPRT"],
                    "the pristine native control changed",
                )
                result["open_status"] = [error, warning]
            elif name == "Author":
                lease = PromptLease(author, out / "PreferenceLease.json")
                lease.enter()
                native_case = {
                    "kind": "corner",
                    "width_m": case["width_mm"] / 1000,
                    "height_m": case["height_mm"] / 1000,
                    "depth_m": case["depth_mm"] / 1000,
                }
                author.build(controller, native_case)
                author.add_equations(case)
                for role, edited in (("Original", False), ("Edited", True)):
                    if edited:
                        author.edit_source(case)
                    observed = author.source_snapshot(case, edited)
                    if edited:
                        same_structure(observed, result["observed"]["Original"])
                    result["observed"][role] = observed
                    target = directory / "Native" / (role + ".SLDPRT")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    require(
                        not target.exists(), "native source save target must be unused"
                    )
                    status = rec.call(
                        "save native equation source " + role,
                        controller.save_as,
                        author.model,
                        target,
                    )
                    require(
                        tuple(status) == (True, 0, 0)
                        and target.is_file()
                        and target.stat().st_size > 0,
                        "native equation source save failed or warned",
                    )
                    result["files"][role] = {
                        "sha256": digest(target),
                        "bytes": target.stat().st_size,
                        "save_status": list(status),
                    }
                    rec.data["result"] = result
                    rec.flush()
                rec.call(
                    "close authored equation source", controller.close_doc, author.model
                )
                author.model = None
                for role, file in result["files"].items():
                    require(
                        digest(directory / "Native" / (role + ".SLDPRT"))
                        == file["sha256"],
                        "native equation source changed during close",
                    )
            else:
                role = "Original" if name == "ReopenOriginal" else "Edited"
                prior = json.loads(
                    (directory / "Inspection" / "Author" / "Result.json").read_bytes()
                )
                require(prior["passed"], "source author phase did not pass")
                source = directory / "Native" / (role + ".SLDPRT")
                require(
                    digest(source) == prior["files"][role]["sha256"],
                    "the immutable native source changed",
                )
                model, error, warning = rec.call(
                    "fresh read-only reopen equation source " + role,
                    controller.open,
                    source,
                    read_only=True,
                )
                require(
                    model is not None
                    and error == warning == 0
                    and Path(author.get(model, "GetPathName")).samefile(source),
                    "the native equation source reopen failed, warned or selected another file",
                )
                author.model = model
                observed = author.source_snapshot(case, role == "Edited")
                same_structure(observed, prior["observed"][role])
                result["observed"][role] = observed
                result["files"][role] = prior["files"][role]
                result["open_status"] = [error, warning]
                require(
                    digest(source) == prior["files"][role]["sha256"],
                    "read-only source observation changed the file",
                )
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if lease is not None:
                try:
                    lease.restore()
                except Exception as error:
                    result["passed"] = False
                    rec.failure(error, cleanup=True)
            if controller is not None:
                try:
                    rec.call("close only owned native source oracle", controller.close)
                except Exception as error:
                    result["passed"] = False
                    rec.failure(error, cleanup=True)
                if controller.diagnostics:
                    result["passed"] = False
                    result["controller_diagnostics"] = controller.diagnostics
    result["dialog_log"] = dialogs.log
    if dialogs.log or rec.data["cleanup_errors"]:
        result["passed"] = False
    result["numeric_checks"] = len(rec.data["checks"])
    rec.data["passed"] = result["passed"]
    rec.data["result"] = result
    rec.flush()
    write_json(out / "Result.json", result)
    public = {
        key: result[key]
        for key in (
            "passed",
            "source_only",
            "writer_output_count",
            "slot",
            "phase",
            "numeric_checks",
            "intent_sha256",
            "prediction_sha256",
        )
    }
    public["oracle_identity"] = result.get("oracle_identity")
    public["record_sha256"] = digest(out / "Record.json")
    public["result_sha256"] = digest(out / "Result.json")
    public["files"] = result["files"]
    if "open_status" in result:
        public["open_status"] = result["open_status"]
    publish_progress(path, slot, name, public)
    return public


def lock_case(path, sha, slot):
    job = read_job(path, sha)
    guest_only(job)
    directory, _, seal = load_case(path, job, slot)
    results = {}
    for name in PHASES:
        result_path = directory / "Inspection" / name / "Result.json"
        record_path = result_path.with_name("Record.json")
        value = json.loads(result_path.read_bytes())
        public = json.loads(
            (path.parent / "Progress" / slot / name / "Record.json").read_bytes()
        )
        require(
            value["passed"]
            and public["passed"]
            and public["result_sha256"] == digest(result_path)
            and public["record_sha256"] == digest(record_path),
            "a required native source phase did not qualify",
        )
        results[name] = public
    identities = [
        (
            row["oracle_identity"]["process_id"],
            row["oracle_identity"]["process_creation_filetime"],
        )
        for row in results.values()
    ]
    require(
        len(set(identities)) == len(PHASES),
        "native source phases did not use five independent process identities",
    )
    originals = results["Author"]["files"]
    for role, source in originals.items():
        require(
            digest(directory / "Native" / (role + ".SLDPRT")) == source["sha256"],
            "the qualified native source changed before locking",
        )
        require(
            results["Reopen" + role]["files"][role] == source,
            "source and fresh reopen file identities differ",
        )
    result = {
        "schema": "kit.sw2026.equation-prewriter-source-lock.v1",
        "slot": slot,
        "heldout_source_locked": slot.startswith("Slot"),
        "source_locked": True,
        "protocol_sha256": sha,
        "intent_sha256": seal["intent_sha256"],
        "prediction_sha256": seal["prediction_sha256"],
        "source_files": originals,
        "phases": results,
        "distinct_native_processes": len(identities),
        "controls_healthy": True,
        "writer_output_count": 0,
        "generated_writer_qualified": False,
        "locked_at": time.time(),
    }
    publish_progress(path, slot, "Lock", result)
    return result


def recover(path, sha, journal_path, output):
    job = read_job(path, sha)
    guest_only(job)
    require(not output.exists(), "preference recovery receipt must be unused")
    state = json.loads(journal_path.read_bytes())
    roots = (path.parent / "Disclosed", Path(job["guest_private_root"]))
    require(
        journal_path.name == "PreferenceLease.json"
        and journal_path.parent.name == "Author"
        and any(
            journal_path.resolve().is_relative_to(root.resolve()) for root in roots
        ),
        "recovery requires this protocol's exact owned author journal",
    )
    require(
        state["schema"] == "kit.sw2026.equation-dimension-prompt-lease.v1"
        and state["protocol_sha256"] == sha
        and state["oracle_identity"]["sha256"] == ORACLE
        and state["preference_enum"] == 10
        and type(state["original"]) is bool
        and state["restore_required"]
        and not state["restored"],
        "the owned preference journal does not require recovery",
    )
    from OracleIdentity import application_identity
    import Swapp

    rec = Recorder(
        output.with_name(output.stem + "Record.json"),
        {
            "protocol_sha256": sha,
            "journal_sha256": digest(journal_path),
            "recovery_only": True,
        },
    )
    controller = None
    result = {
        "passed": False,
        "documents_opened": 0,
        "document_setters": 0,
        "document_saves": 0,
    }
    try:
        rec.call("verify idle oracle before preference recovery", Swapp.sweep)
        controller = rec.call("start exact preference recovery session", Swapp.Sw)
        identity = rec.call(
            "verify preference recovery process", application_identity, controller.app
        )
        require(
            identity["sha256"] == ORACLE and identity["version_matches"],
            "preference recovery oracle differs",
        )
        result["oracle_identity"] = identity
        rec.call(
            "restore captured original dimension prompt",
            Swapp.invoke,
            controller.app,
            "SetUserPreferenceToggle",
            10,
            state["original"],
        )
        actual = bool(
            rec.call(
                "verify restored dimension prompt",
                Swapp.invoke,
                controller.app,
                "GetUserPreferenceToggle",
                10,
            )
        )
        require(
            actual == state["original"],
            "dimension prompt recovery did not retain the captured original",
        )
        result["restored_original"] = actual
        result["passed"] = True
    except Exception as error:
        rec.failure(error)
    finally:
        if controller is not None:
            controller.close()
            if controller.diagnostics:
                result["passed"] = False
                result["controller_diagnostics"] = controller.diagnostics
    write_new(output, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify")
    for command in ("seal", "lock"):
        commands.add_parser(command).add_argument(
            "--slot", choices=tuple(SLOTS), required=True
        )
    active = commands.add_parser("phase")
    active.add_argument("--slot", choices=tuple(SLOTS), required=True)
    active.add_argument("--phase", choices=PHASES, required=True)
    recovery = commands.add_parser("recover")
    recovery.add_argument("--journal", type=Path, required=True)
    recovery.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "verify":
        job = read_job(args.job, args.sha256)
        result = {
            "passed": True,
            "protocol_sha256": args.sha256,
            "file_count": len(job["files_sha256"]),
            "native_processes_started": 0,
            "sealed_inputs_read": 0,
        }
    elif args.command == "seal":
        result = seal_intents(args.job, args.sha256, args.slot)
    elif args.command == "phase":
        result = phase(args.job, args.sha256, args.slot, args.phase)
    elif args.command == "lock":
        result = lock_case(args.job, args.sha256, args.slot)
    else:
        result = recover(args.job, args.sha256, args.journal, args.output)
    print(json.dumps(result, sort_keys=True))
    return (
        0
        if result.get(
            "passed",
            result.get("source_locked", result.get("native_processes_started") == 0),
        )
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
