from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path


class EvidenceFailure(RuntimeError):
    pass


class PendingCapability(RuntimeError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tool_hashes():
    directory = Path(__file__).resolve().parent
    return {name: digest(directory / name) for name in ("AuthorCurves.py", "Swapp.py", "OracleIdentity.py")}


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(safe_result(value), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def require(condition, message):
    if not condition:
        raise EvidenceFailure(message)


def application_pids():
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq SLDWORKS.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True, check=True,
    )
    return {
        int(row[1].replace(",", ""))
        for row in csv.reader(io.StringIO(result.stdout))
        if len(row) > 1 and row[0].casefold() == "sldworks.exe"
    }


def wait_exit(process_id, timeout=30):
    deadline = time.monotonic() + timeout
    while process_id in application_pids():
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.25)
    return True


def safe_result(value):
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, (list, tuple)):
        return [safe_result(item) for item in value]
    if isinstance(value, dict):
        return {str(key): safe_result(item) for key, item in value.items()}
    return {"returned_object": type(value).__name__}


class Recorder:
    def __init__(self, path, job):
        self.path = Path(path)
        self.data = {
            "schema": "kit-sw2026-curve-source-phase/1", "job": job,
            "stage": "starting", "api_calls": [], "checks": [],
            "first_failure": None, "cleanup_errors": [], "passed": False,
            "started_at": time.time(),
        }
        self.flush()

    def flush(self):
        write_json(self.path, self.data)

    def call(self, label, function, *args, parameters=None, **kwargs):
        self.data["stage"] = label
        entry = {"method": label, "arguments": safe_result(args) if parameters is None else parameters}
        if kwargs:
            entry["keyword_arguments"] = safe_result(kwargs)
        self.data["api_calls"].append(entry)
        self.flush()
        started = time.monotonic()
        try:
            result = function(*args, **kwargs)
        except Exception as error:
            entry.update(error=repr(error), seconds=time.monotonic() - started)
            self.failure(error)
            raise
        entry.update(result=safe_result(result), seconds=time.monotonic() - started)
        self.flush()
        return result

    def failure(self, error, *, cleanup=False):
        item = {"stage": self.data["stage"], "type": type(error).__name__, "error": repr(error), "pending_capability": isinstance(error, (PendingCapability, AttributeError, NotImplementedError))}
        if cleanup:
            self.data["cleanup_errors"].append(item)
        if self.data["first_failure"] is None:
            self.data["first_failure"] = item
            self.data["traceback"] = traceback.format_exc()
        self.flush()

    def close_number(self, label, actual, expected, *, absolute=1e-12):
        actual, expected = float(actual), float(expected)
        passed = math.isfinite(actual) and math.isclose(actual, expected, rel_tol=2e-7, abs_tol=absolute)
        self.data["checks"].append({"name": label, "actual": actual, "expected": expected, "passed": passed})
        self.flush()
        require(passed, f"{label}: {actual!r} differs from {expected!r}")


def circles(profile):
    kind = profile["kind"]
    if kind == "circle":
        return [{"center_mm": profile["center_mm"], "radius_mm": profile["radius_mm"]}]
    if kind == "annulus":
        return [{"center_mm": profile["center_mm"], "radius_mm": radius} for radius in profile["radii_mm"]]
    if kind == "circles":
        return profile["circles"]
    return []


def entities(case):
    profile = case["profile"]
    kind = profile["kind"]
    result = []
    for index, circle in enumerate(circles(profile)):
        result.append({"kind": "circle", "center": [value / 1000 for value in circle["center_mm"]], "radius": circle["radius_mm"] / 1000, "role": f"curve-{index}", "construction": False})
    if kind == "segment":
        center = [value / 1000 for value in profile["center_mm"]]
        radius = profile["radius_mm"] / 1000
        start = math.radians(profile["start_deg"])
        sweep = math.radians(profile["sweep_deg"]) * profile["direction"]
        p1 = [center[0] + radius * math.cos(start), center[1] + radius * math.sin(start)]
        p2 = [center[0] + radius * math.cos(start + sweep), center[1] + radius * math.sin(start + sweep)]
        result.extend([
            {"kind": "arc", "center": center, "radius": radius, "start": p1, "end": p2, "direction": profile["direction"], "role": "curve-0", "construction": False},
            {"kind": "line", "start": p2, "end": p1, "construction": False},
        ])
    if kind == "capsule":
        center = [value / 1000 for value in profile["center_mm"]]
        radius = profile["radius_mm"] / 1000
        length = profile["center_spacing_mm"] / 1000
        angle = math.radians(profile["rotation_deg"])
        axis = [math.cos(angle), math.sin(angle)]
        normal = [-axis[1], axis[0]]
        left = [center[i] - axis[i] * length / 2 for i in range(2)]
        right = [center[i] + axis[i] * length / 2 for i in range(2)]
        lt, lb = ([left[i] + sign * normal[i] * radius for i in range(2)] for sign in (1, -1))
        rt, rb = ([right[i] + sign * normal[i] * radius for i in range(2)] for sign in (1, -1))
        result.extend([
            {"kind": "arc", "center": left, "radius": radius, "start": lt, "end": lb, "direction": 1, "role": "curve-0", "construction": False},
            {"kind": "line", "start": lb, "end": rb, "construction": False},
            {"kind": "arc", "center": right, "radius": radius, "start": rb, "end": rt, "direction": 1, "construction": False},
            {"kind": "line", "start": rt, "end": lt, "construction": False},
        ])
    if kind == "rectangle":
        cx, cy = (value / 1000 for value in profile["center_mm"])
        width, height = profile["width_mm"] / 1000, profile["height_mm"] / 1000
        points = [[cx - width / 2, cy - height / 2], [cx + width / 2, cy - height / 2], [cx + width / 2, cy + height / 2], [cx - width / 2, cy + height / 2]]
        result.extend({"kind": "line", "start": points[index], "end": points[(index + 1) % 4], "construction": False} for index in range(4))
    for item in profile.get("construction_arcs", []):
        arc_case = {"profile": {"kind": "segment", **item}}
        arc = entities(arc_case)[0]
        arc.pop("role", None)
        arc["construction"] = True
        result.append(arc)
    require(bool(result), f"unsupported or empty profile {kind}")
    return result


def planar_properties(case):
    profile = case["profile"]
    kind = profile["kind"]
    if kind in ("circle", "circles"):
        items = circles(profile)
        weights = [math.pi * (item["radius_mm"] / 1000) ** 2 for item in items]
        area = sum(weights)
        perimeter = sum(2 * math.pi * item["radius_mm"] / 1000 for item in items)
        center = [sum(weight * item["center_mm"][axis] / 1000 for weight, item in zip(weights, items)) / area for axis in range(2)]
    elif kind == "annulus":
        outer, inner = (value / 1000 for value in profile["radii_mm"])
        require(outer > inner > 0, "annulus radii must be ordered and positive")
        area, perimeter = math.pi * (outer * outer - inner * inner), 2 * math.pi * (outer + inner)
        center = [value / 1000 for value in profile["center_mm"]]
    elif kind == "segment":
        radius = profile["radius_mm"] / 1000
        angle = math.radians(profile["sweep_deg"])
        require(0 < angle < 2 * math.pi, "arc sweep must be strictly between zero and a full turn")
        area = radius * radius * (angle - math.sin(angle)) / 2
        perimeter = radius * angle + 2 * radius * math.sin(angle / 2)
        offset = 4 * radius * math.sin(angle / 2) ** 3 / (3 * (angle - math.sin(angle)))
        direction = math.radians(profile["start_deg"]) + profile["direction"] * angle / 2
        center = [profile["center_mm"][0] / 1000 + offset * math.cos(direction), profile["center_mm"][1] / 1000 + offset * math.sin(direction)]
    elif kind == "capsule":
        radius, length = profile["radius_mm"] / 1000, profile["center_spacing_mm"] / 1000
        area, perimeter = math.pi * radius * radius + 2 * radius * length, 2 * math.pi * radius + 2 * length
        center = [value / 1000 for value in profile["center_mm"]]
    elif kind == "rectangle":
        width, height = profile["width_mm"] / 1000, profile["height_mm"] / 1000
        area, perimeter = width * height, 2 * (width + height)
        center = [value / 1000 for value in profile["center_mm"]]
    else:
        raise EvidenceFailure(f"no independent geometry formula for {kind}")
    return area, perimeter, center


def edited_case(case):
    result = copy.deepcopy(case)
    target, factor = result["edit"]["target"], result["edit"]["factor"]
    if target == "depth":
        result["depth_mm"] *= factor
    else:
        index = int(target.removeprefix("curve-"))
        profile = result["profile"]
        if profile["kind"] == "annulus":
            profile["radii_mm"][index] *= factor
        elif profile["kind"] == "circles":
            profile["circles"][index]["radius_mm"] *= factor
        else:
            require(index == 0, "single-curve edit index must be zero")
            profile["radius_mm"] *= factor
    return result


def relation_intent(case):
    descriptors = entities(case)
    result = [
        (17, [f"entity-{index}.center"])
        for index, item in enumerate(descriptors)
        if item["kind"] != "line" and not item["construction"]
    ]
    if case["profile"]["kind"] in ("segment", "capsule"):
        for index in range(len(descriptors)):
            next_index = (index + 1) % len(descriptors)
            result.append((9, [f"entity-{index}.end", f"entity-{next_index}.start"]))
            if case["profile"]["kind"] == "capsule":
                result.append((6, [f"entity-{index}", f"entity-{next_index}"]))
        if case["profile"]["kind"] == "capsule":
            result.append((14, ["entity-0", "entity-2"]))
    return result


def binding_key(binding):
    require(isinstance(binding, dict), "native entity binding must be an object")
    kind = binding.get("kind")
    require(
        kind in ("point", "line", "arc"),
        "native entity binding has an unsupported geometry kind",
    )
    expected = {"kind", "id"} if kind == "point" else {"kind", "id", "segment_type"}
    require(
        set(binding) == expected,
        "native entity binding fields differ from the identity schema",
    )
    identity = binding["id"]
    require(
        isinstance(identity, (list, tuple))
        and len(identity) == 2
        and all(type(value) is int for value in identity),
        "native GetID must supply two integer identity components",
    )
    segment_type = -1 if kind == "point" else binding["segment_type"]
    require(
        kind == "point"
        or type(segment_type) is int
        and segment_type == (0 if kind == "line" else 1),
        "native segment kind and GetType disagree",
    )
    return kind, segment_type, *identity


def relation_key(kind, bindings):
    require(
        type(kind) is int and kind in (9, 17, 6, 14),
        "relation binding verification supports only the four authored relation kinds",
    )
    require(
        isinstance(bindings, list) and len(bindings) == (1 if kind == 17 else 2),
        "relation binding count differs from the authored relation kind",
    )
    keys = tuple(binding_key(binding) for binding in bindings)
    require(
        all((key[0] == "point") == (kind in (9, 17)) for key in keys),
        "relation entity namespace differs from its authored kind",
    )
    return kind, tuple(sorted(keys))


class CurveAuthor:
    def __init__(self, application, recorder, modules):
        self.app = application
        self.rec = recorder
        self.sw = modules
        self.model = None
        self.sketch = None
        self.dimensions = []
        self.dimension_objects = {}
        self.relations = []
        self.segment_sources = {}
        self.interfaces = self.rec.call(
            "load 2026 type library", self.sw.wc.gencache.EnsureModule,
            "{83A33D31-27C5-11CE-BFD4-00400513BB57}", 0, 34, 0,
            bForDemand=False,
            parameters={"library": "{83A33D31-27C5-11CE-BFD4-00400513BB57}", "lcid": 0, "major": 34, "minor": 0, "demand": False},
        )
        self.rec.data["com_type_library"] = {
            "guid": str(self.interfaces.CLSID), "lcid": self.interfaces.LCID,
            "major": self.interfaces.MajorVersion, "minor": self.interfaces.MinorVersion,
        }
        self.rec.flush()

    def get(self, obj, name, *args):
        function = self.sw.invoke if args else self.sw.cv
        parameters = {"values": safe_result(args), "dispatch_class": type(obj).__module__ + "." + type(obj).__name__, "binding": "untyped-method" if args else "property-or-zero-argument-method"}
        return self.rec.call(name, function, obj, name, *args, parameters=parameters)

    def set(self, obj, name, value):
        self.rec.call("set " + name, setattr, obj, name, value, parameters={"value": value})
        require(self.get(obj, name) == value, f"native property {name} did not retain its requested value")

    def typed(self, value, kind):
        try:
            target = getattr(self.interfaces, kind)
            target = getattr(target, "default_interface", target)
            proxy = self.rec.call(
                "QueryInterface " + kind, value._oleobj_.QueryInterface,
                target.CLSID, self.sw.pythoncom.IID_IDispatch,
                parameters={"interface": kind, "iid": str(target.CLSID), "binding": "explicit registered 2026 type library"},
            )
            return target(proxy)
        except Exception as error:
            raise PendingCapability(f"type-library cast to {kind} is unavailable: {error!r}") from error

    def point(self, point):
        return [float(self.get(point, name)) for name in ("X", "Y", "Z")]

    def entity_binding(self, value, namespace):
        require(value is not None, "native relation entity is null")
        if namespace == "point":
            self.typed(value, "SketchPoint")
            result = {"kind": "point"}
        else:
            require(namespace == "segment", "unsupported native entity namespace")
            kind = int(self.get(value, "GetType"))
            require(kind in (0, 1), f"unsupported native segment GetType: {kind}")
            self.typed(value, "SketchLine" if kind == 0 else "SketchArc")
            result = {"kind": "line" if kind == 0 else "arc", "segment_type": kind}
        result["id"] = list(self.get(value, "GetID"))
        binding_key(result)
        return result

    def relation_source(self, label):
        match = re.fullmatch(r"(entity-[0-9]+)(?:\.(start|end|center))?", label)
        require(
            match is not None and match[1] in self.segment_sources,
            f"requested entity has no native segment source: {label}",
        )
        result = {"segment": copy.deepcopy(self.segment_sources[match[1]])}
        if match[2] is not None:
            result["point"] = match[2]
        return result

    def observe_relation(self, relation, result):
        try:
            result["type"] = int(self.get(relation, "GetRelationType"))
            result["entities"] = int(self.get(relation, "GetEntitiesCount"))
            result["entity_ids"] = []
            result["bindings"] = [] if result["type"] in (9, 17, 6, 14) else None
            self.rec.flush()
            related = list(self.get(relation, "GetEntities") or [])
            result["returned_entities"] = len(related)
            self.rec.flush()
            require(
                len(related) == result["entities"],
                "native relation count differs from its returned entities",
            )
            for value in related:
                if result["bindings"] is None:
                    result["entity_ids"].append(safe_result(self.get(value, "GetID")))
                else:
                    binding = self.entity_binding(
                        value, "point" if result["type"] in (9, 17) else "segment"
                    )
                    result["bindings"].append(binding)
                    result["entity_ids"].append(list(binding["id"]))
                self.rec.flush()
            result["suppressed"] = bool(self.get(relation, "Suppressed"))
            self.rec.flush()
            if result["bindings"] is not None:
                relation_key(result["type"], result["bindings"])
        except Exception as error:
            result["observation_error"] = repr(error)
            self.rec.flush()
            raise
        return result

    def relation(self, kind, values, labels):
        require(
            type(kind) is int and kind in (9, 17, 6, 14),
            "unsupported authored relation kind",
        )
        require(
            len(values) == len(labels) == (1 if kind == 17 else 2),
            "authored relation values and labels differ",
        )
        request = {
            "binding_schema": 1,
            "type": kind,
            "entities": list(labels),
            "bindings": [],
            "sources": [],
            "mode": "requesting",
        }
        self.relations.append(request)
        self.rec.data["requested_relations"] = self.relations
        self.rec.flush()
        for value, label in zip(values, labels):
            request["bindings"].append(
                self.entity_binding(value, "point" if kind in (9, 17) else "segment")
            )
            request["sources"].append(self.relation_source(label))
            self.rec.flush()
        expected = relation_key(kind, request["bindings"])
        if kind == 9 and binding_key(request["bindings"][0]) == binding_key(
            request["bindings"][1]
        ):
            request["mode"] = "shared-point"
            self.rec.flush()
            return
        array = self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_DISPATCH, values)
        manager = self.get(self.sketch, "RelationManager")
        relation = self.rec.call(
            "ISketchRelationManager.AddRelation",
            self.sw.invoke,
            manager,
            "AddRelation",
            array,
            kind,
            parameters={
                "entities": labels,
                "entity_bindings": request["bindings"],
                "type": kind,
                "binding": "untyped-method",
            },
        )
        if relation is None:
            raise PendingCapability(f"relation type {kind} returned no relation for {labels}")
        request["returned"] = {}
        self.rec.flush()
        returned = self.observe_relation(relation, request["returned"])
        require(returned["type"] == kind, "native relation type differs from request")
        require(
            returned["entities"] == len(values),
            "native relation entity count differs from request",
        )
        require(not returned["suppressed"], "new native relation is suppressed")
        require(
            relation_key(kind, returned["bindings"]) == expected,
            "native relation entities differ from the exact requested bindings",
        )
        request["mode"] = "native-relation"
        self.rec.flush()

    def load_relation_bindings(self, case, requests):
        validation = {
            "binding_schema": 1,
            "required_intent": relation_intent(case),
            "requests": safe_result(requests),
            "validated": False,
        }
        self.rec.data["requested_relation_validation"] = validation
        self.rec.flush()
        require(
            isinstance(requests, list),
            "verification requires recorded native relation bindings",
        )
        require(
            all(isinstance(item, dict) for item in requests),
            "recorded relation requests must be binding objects",
        )
        require(
            [(item.get("type"), item.get("entities")) for item in requests]
            == relation_intent(case),
            "recorded requests differ from the neutral source's complete relation intent",
        )
        descriptors = entities(case)
        for item in requests:
            require(
                type(item.get("binding_schema")) is int and item["binding_schema"] == 1,
                "verification requires the native relation binding schema",
            )
            key = relation_key(item["type"], item.get("bindings"))
            require(
                isinstance(item.get("sources"), list)
                and len(item["sources"]) == len(item["bindings"]),
                "relation bindings require one native geometry source per entity",
            )
            for label, binding, source in zip(
                item["entities"], item["bindings"], item["sources"]
            ):
                match = re.fullmatch(r"entity-([0-9]+)(?:\.(start|end|center))?", label)
                require(
                    match is not None and int(match[1]) < len(descriptors),
                    "relation entity label has no neutral descriptor",
                )
                require(
                    isinstance(source, dict)
                    and set(source)
                    == ({"segment", "point"} if match[2] else {"segment"}),
                    "relation source fields differ from its entity role",
                )
                segment = binding_key(source["segment"])
                expected_kind = (
                    "line" if descriptors[int(match[1])]["kind"] == "line" else "arc"
                )
                require(
                    segment[0] == expected_kind,
                    "relation source uses the wrong native segment namespace",
                )
                if match[2]:
                    require(
                        binding["kind"] == "point" and source["point"] == match[2],
                        "relation point source differs from its requested endpoint or centre role",
                    )
                else:
                    require(
                        binding_key(binding) == segment,
                        "relation segment source differs from its requested binding",
                    )
            if item.get("mode") == "shared-point":
                require(
                    item["type"] == 9
                    and binding_key(item["bindings"][0])
                    == binding_key(item["bindings"][1]),
                    "shared-point coincidence lacks exact point identity",
                )
            else:
                require(
                    item.get("mode") == "native-relation"
                    and isinstance(item.get("returned"), dict),
                    "verification requires a completed native relation request",
                )
                returned = item["returned"]
                require(
                    returned.get("type") == item["type"]
                    and returned.get("entities")
                    == returned.get("returned_entities")
                    == len(item["bindings"])
                    and returned.get("suppressed") is False
                    and relation_key(item["type"], returned.get("bindings")) == key,
                    "recorded returned relation did not match its requested bindings",
                )
        self.relations = copy.deepcopy(requests)
        validation["validated"] = True
        self.rec.data["requested_relations"] = self.relations
        self.rec.flush()

    def verify_relations(self, actual, verification):
        manager = self.get(self.sketch, "RelationManager")
        observed = verification["observed"]
        for relation in self.get(manager, "GetRelations", 0) or []:
            observed.append({})
            self.rec.flush()
            self.observe_relation(relation, observed[-1])
        require(
            not any(item["suppressed"] for item in observed),
            "source sketch has suppressed relations",
        )
        geometry = {}
        for item in actual:
            key = binding_key(item["binding"])
            require(
                key not in geometry,
                "native geometry repeats an entity identity within its segment namespace",
            )
            geometry[key] = item
        used = set()
        for index, request in enumerate(self.relations):
            evidence = {
                "request_index": index,
                "type": request["type"],
                "mode": request["mode"],
                "requested_bindings": request["bindings"],
                "resolved_sources": [],
                "matched": False,
            }
            verification["requests"].append(evidence)
            self.rec.flush()
            for source in request["sources"]:
                segment = geometry.get(binding_key(source["segment"]))
                require(
                    segment is not None,
                    "a requested relation's native segment source is missing",
                )
                resolved = (
                    segment["point_bindings"].get(source["point"])
                    if "point" in source
                    else segment["binding"]
                )
                require(
                    resolved is not None,
                    "a requested relation's endpoint or centre source is unavailable",
                )
                evidence["resolved_sources"].append(resolved)
                self.rec.flush()
            evidence["sources_match_requested_bindings"] = all(
                binding_key(left) == binding_key(right)
                for left, right in zip(
                    evidence["resolved_sources"], request["bindings"]
                )
            )
            self.rec.flush()
            require(
                evidence["sources_match_requested_bindings"],
                "a requested relation's native source identity changed",
            )
            if request["mode"] == "shared-point":
                evidence["shared_point_still_identical"] = binding_key(
                    evidence["resolved_sources"][0]
                ) == binding_key(evidence["resolved_sources"][1])
                self.rec.flush()
                require(
                    evidence["shared_point_still_identical"],
                    "shared-point coincidence was not retained",
                )
            else:
                expected = relation_key(request["type"], request["bindings"])
                matches = [
                    offset
                    for offset, item in enumerate(observed)
                    if item["type"] == request["type"]
                    and relation_key(item["type"], item["bindings"]) == expected
                ]
                available = [offset for offset in matches if offset not in used]
                evidence["matching_relation_indices"] = matches
                if available:
                    selected = available[0]
                elif request["type"] in (9, 17) and matches:
                    selected = matches[0]
                else:
                    selected = None
                evidence["matched_relation_index"] = selected
                evidence["reused_exact_point_constraint"] = (
                    selected in used if selected is not None else False
                )
                self.rec.flush()
                require(
                    selected is not None,
                    "required native relation type and exact entity bindings were not retained",
                )
                used.add(selected)
            evidence["matched"] = True
            self.rec.flush()
        for selector in (1, 2, 6):
            rejected = self.get(manager, "GetRelations", selector) or []
            verification["invalid_filters"].append(
                {"selector": selector, "count": len(rejected)}
            )
            self.rec.flush()
            require(
                not rejected,
                f"sketch has dangling, overdefining or broken relations: filter {selector}",
            )
        verification["passed"] = True
        self.rec.flush()
        return observed

    def dimension(self, segment, role, value, kind, location):
        self.get(self.model, "ClearSelection2", True)
        require(bool(self.get(segment, "Select4", False, self.sw.nothing())), "dimension entity selection failed")
        method = "AddDiameterDimension2" if kind == "diameter" else "AddRadialDimension2"
        display = self.get(self.model, method, location[0], location[1], 0.0)
        require(display is not None, "dimension creation returned no display dimension")
        dimension = self.get(display, "GetDimension2", 0)
        require(dimension is not None, "display dimension has no dimension")
        require(int(self.get(dimension, "DrivenState")) == 2, "new dimension is not driving")
        status = int(self.get(dimension, "SetSystemValue3", value, 1, self.sw.nothing()))
        require(status == 0, f"dimension setter failed with status {status}")
        self.rec.close_number(role, self.get(dimension, "SystemValue"), value)
        self.dimensions.append({"role": role, "name": str(self.get(dimension, "FullName")), "value": value, "kind": kind})
        self.dimension_objects[role] = dimension
        self.get(self.model, "ClearSelection2", True)

    def refresh_dimension_names(self):
        for item in self.dimensions:
            dimension = self.dimension_objects[item["role"]]
            full_name = str(self.get(dimension, "FullName"))
            parts = full_name.split("@")
            feature = "CurveBoss" if item["role"] == "depth" else "CurveSketch"
            require(len(parts) >= 2 and parts[1] == feature, f"dimension does not belong to its renamed feature: {full_name}")
            item.update(name=parts[0] + "@" + feature, full_name=full_name)
        self.rec.data["dimensions"] = self.dimensions
        self.rec.flush()

    def created_sketch_feature(self):
        matches = []
        feature = self.get(self.model, "FirstFeature")
        while feature is not None:
            if str(self.get(feature, "GetTypeName2")) == "ProfileFeature":
                matches.append(feature)
            feature = self.get(feature, "GetNextFeature")
        require(len(matches) == 1, "new part must contain exactly one authored 2D sketch feature")
        require(self.get(matches[0], "GetSpecificFeature2") is not None, "authored profile has no specific sketch interface")
        return matches[0]

    def build(self, case, session):
        template = str(self.get(self.app, "GetUserPreferenceStringValue", 8))
        self.model = self.get(self.app, "NewDocument", template, 0, 0, 0)
        require(self.model is not None, "native new part creation returned no document")
        plane = {"front": "Front Plane", "top": "Top Plane", "right": "Right Plane"}[case["plane"]]
        selected = self.get(self.get(self.model, "Extension"), "SelectByID2", plane, "PLANE", 0.0, 0.0, 0.0, False, 0, self.sw.nothing(), 0)
        require(bool(selected), "sketch plane selection failed")
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        self.sketch = self.get(manager, "ActiveSketch")
        require(self.sketch is not None, "no active sketch after insertion")
        self.set(manager, "AddToDB", True)
        created = []
        descriptors = entities(case)
        try:
            if case.get("creation") == "rectangle-control":
                points = [item["start"] for item in descriptors]
                rectangle = self.get(manager, "CreateCornerRectangle", *points[0], 0.0, *points[2], 0.0)
                require(rectangle is not None and len(rectangle) == 4, "independent rectangle creation failed")
                created = list(rectangle)
            else:
                for item in descriptors:
                    kind = item["kind"]
                    if kind == "circle":
                        x, y = item["center"]
                        if case.get("creation") == "point-circle-control":
                            segment = self.get(manager, "CreateCircle", x, y, 0.0, x + item["radius"], y, 0.0)
                        else:
                            segment = self.get(manager, "CreateCircleByRadius", x, y, 0.0, item["radius"])
                    elif kind == "arc":
                        segment = self.get(manager, "CreateArc", *item["center"], 0.0, *item["start"], 0.0, *item["end"], 0.0, item["direction"])
                    else:
                        segment = self.get(manager, "CreateLine", *item["start"], 0.0, *item["end"], 0.0)
                    require(segment is not None, f"{kind} creation returned no segment")
                    self.set(segment, "ConstructionGeometry", item["construction"])
                    created.append(segment)
        finally:
            self.set(manager, "AddToDB", False)
        typed = [self.typed(segment, "SketchLine" if item["kind"] == "line" else "SketchArc") for item, segment in zip(descriptors, created)]
        self.segment_sources = {
            f"entity-{index}": self.entity_binding(segment, "segment")
            for index, segment in enumerate(created)
        }
        self.rec.data["authored_segment_bindings"] = self.segment_sources
        self.rec.flush()
        for index, (item, segment) in enumerate(zip(descriptors, typed)):
            if item["kind"] != "line" and not item["construction"]:
                self.relation(17, [self.get(segment, "GetCenterPoint2")], [f"entity-{index}.center"])
        if case["profile"]["kind"] in ("segment", "capsule"):
            for index in range(len(typed)):
                next_index = (index + 1) % len(typed)
                self.relation(9, [self.get(typed[index], "GetEndPoint2"), self.get(typed[next_index], "GetStartPoint2")], [f"entity-{index}.end", f"entity-{next_index}.start"])
                if case["profile"]["kind"] == "capsule":
                    self.relation(6, [created[index], created[next_index]], [f"entity-{index}", f"entity-{next_index}"])
            if case["profile"]["kind"] == "capsule":
                self.relation(14, [created[0], created[2]], ["entity-0", "entity-2"])
        for item, segment in zip(descriptors, created):
            if "role" in item:
                kind = case.get("dimension_kind", "radial")
                value = item["radius"] * (2 if kind == "diameter" else 1)
                at = [item["center"][0] + item["radius"] * 1.7, item["center"][1] + item["radius"] * 1.3]
                self.dimension(segment, item["role"], value, kind, at)
        self.get(manager, "InsertSketch", True)
        sketch_feature = self.created_sketch_feature()
        self.set(sketch_feature, "Name", "CurveSketch")
        self.get(self.model, "ClearSelection2", True)
        require(bool(self.get(sketch_feature, "Select2", False, 0)), "extrusion sketch selection failed")
        arguments = [True, False, case["reverse"], 0, 0, case["depth_mm"] / 1000, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False]
        boss = self.get(self.get(self.model, "FeatureManager"), "FeatureExtrusion3", *arguments)
        require(boss is not None, "blind extrusion returned no feature")
        self.set(boss, "Name", "CurveBoss")
        display = self.get(boss, "GetFirstDisplayDimension")
        require(display is not None, "extrusion has no editable depth dimension")
        dimension = self.get(display, "GetDimension2", 0)
        self.rec.close_number("depth dimension", self.get(dimension, "SystemValue"), case["depth_mm"] / 1000)
        self.dimensions.append({"role": "depth", "name": str(self.get(dimension, "FullName")), "value": case["depth_mm"] / 1000, "kind": "linear"})
        self.dimension_objects["depth"] = dimension
        self.refresh_dimension_names()
        self.rec.data.update(dimensions=self.dimensions, requested_relations=self.relations)
        self.rec.flush()

    def geometry(self):
        result = []
        for segment in self.get(self.sketch, "GetSketchSegments") or []:
            kind = int(self.get(segment, "GetType"))
            require(kind in (0, 1), f"unexpected sketch segment type {kind}")
            obj = self.typed(segment, "SketchLine" if kind == 0 else "SketchArc")
            binding = self.entity_binding(segment, "segment")
            item = {
                "construction": bool(self.get(segment, "ConstructionGeometry")),
                "id": list(binding["id"]),
                "binding": binding,
                "point_bindings": {},
            }
            if kind == 0:
                start, end = self.get(obj, "GetStartPoint2"), self.get(
                    obj, "GetEndPoint2"
                )
                item.update(
                    kind="line", start=self.point(start)[:2], end=self.point(end)[:2]
                )
                item["point_bindings"].update(
                    start=self.entity_binding(start, "point"),
                    end=self.entity_binding(end, "point"),
                )
            else:
                center = self.get(obj, "GetCenterPoint2")
                item.update(
                    kind="circle" if bool(self.get(obj, "IsCircle")) else "arc",
                    center=self.point(center)[:2],
                    radius=float(self.get(obj, "GetRadius")),
                )
                item["point_bindings"]["center"] = self.entity_binding(center, "point")
                if item["kind"] == "arc":
                    start, end = self.get(obj, "GetStartPoint2"), self.get(
                        obj, "GetEndPoint2"
                    )
                    item.update(
                        start=self.point(start)[:2],
                        end=self.point(end)[:2],
                        direction=int(self.get(obj, "GetRotationDir")),
                    )
                    item["point_bindings"].update(
                        start=self.entity_binding(start, "point"),
                        end=self.entity_binding(end, "point"),
                    )
            result.append(item)
        return result

    def check_geometry(self, case, actual):
        expected = entities(case)
        require(len(actual) == len(expected), "sketch entity count differs from neutral input")
        remaining = list(actual)
        for item in expected:
            matches = []
            for index, candidate in enumerate(remaining):
                if candidate["kind"] != item["kind"] or candidate["construction"] != item["construction"]:
                    continue
                keys = ("start", "end") if item["kind"] == "line" else ("center", "radius")
                def same(left, right):
                    if isinstance(left, list):
                        return all(math.isclose(a, b, rel_tol=2e-7, abs_tol=1e-10) for a, b in zip(left, right))
                    return math.isclose(left, right, rel_tol=2e-7, abs_tol=1e-12)
                good = all(same(item[key], candidate[key]) for key in keys)
                if item["kind"] == "line":
                    good = good or (same(item["start"], candidate["end"]) and same(item["end"], candidate["start"]))
                if item["kind"] == "arc":
                    good = good and item["direction"] == candidate["direction"] and same(item["start"], candidate["start"]) and same(item["end"], candidate["end"])
                if good:
                    matches.append(index)
            require(len(matches) == 1, f"sketch geometry is missing or ambiguous: {item}")
            remaining.pop(matches[0])

    def feature_tree(self):
        result, visited = [], set()
        def visit(feature, parent):
            traversed = 0
            while feature is not None:
                traversed += 1
                require(traversed <= 1000, "feature sibling traversal exceeded its bound")
                name, kind = str(self.get(feature, "Name")), str(self.get(feature, "GetTypeName2"))
                key = (name, kind)
                if key not in visited:
                    require(len(visited) < 1000, "feature traversal exceeded its bound")
                    visited.add(key)
                    warning = self.sw.byref_bool()
                    error = self.get(feature, "GetErrorCode2", warning)
                    code, is_warning = (int(error[0]), bool(error[1])) if isinstance(error, tuple) else (int(error), bool(warning.value))
                    suppressed = bool(self.get(feature, "IsSuppressed"))
                    item = {"name": name, "type": kind, "parent": parent, "error": code, "warning": is_warning, "suppressed": suppressed}
                    result.append(item)
                    require(code == 0 and not is_warning, f"native feature error or warning: {item}")
                    if name in ("CurveSketch", "CurveBoss"):
                        require(not suppressed, f"authored feature is suppressed: {name}")
                    visit(self.get(feature, "GetFirstSubFeature"), name)
                feature = self.get(feature, "GetNextFeature" if parent is None else "GetNextSubFeature")
        visit(self.get(self.model, "FirstFeature"), None)
        require({"CurveSketch", "CurveBoss"} <= {item["name"] for item in result}, "authored feature tree is incomplete")
        return result

    def snapshot(self, case, label):
        require(bool(self.get(self.model, "ForceRebuild3", False)), "native rebuild returned failure")
        wrong = int(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount"))
        require(wrong == 0, f"native document has {wrong} rebuild problems")
        sketch_feature = self.get(self.model, "FeatureByName", "CurveSketch")
        require(sketch_feature is not None, "saved sketch cannot be found")
        self.sketch = self.get(sketch_feature, "GetSpecificFeature2")
        actual = self.geometry()
        verification = {
            "binding_schema": 1,
            "observed": [],
            "requests": [],
            "invalid_filters": [],
            "passed": False,
        }
        snapshot = {
            "geometry": actual,
            "relations": verification["observed"],
            "relation_verification": verification,
        }
        self.rec.data[label] = snapshot
        self.rec.flush()
        self.check_geometry(case, actual)
        self.load_relation_bindings(case, self.relations)
        relations = self.verify_relations(actual, verification)
        boss = self.get(self.model, "FeatureByName", "CurveBoss")
        definition = self.get(boss, "GetDefinition")
        require(definition is not None, "extrusion definition is unavailable")
        extrusion = {"depth": float(self.get(definition, "GetDepth", True)), "end": int(self.get(definition, "GetEndCondition", True)), "both_directions": bool(self.get(definition, "BothDirections")), "reverse": bool(self.get(definition, "ReverseDirection"))}
        require(extrusion["end"] == 0 and not extrusion["both_directions"] and extrusion["reverse"] == case["reverse"], "extrusion definition differs from blind input")
        self.rec.close_number("extrusion depth", extrusion["depth"], case["depth_mm"] / 1000)
        body_objects = self.get(self.model, "GetBodies2", 0, False) or []
        require(len(body_objects) == case["expected_bodies"] > 0, "native solid body count differs from input")
        properties = self.get(self.get(self.model, "Extension"), "CreateMassProperty")
        require(properties is not None, "mass properties are unavailable")
        self.set(properties, "UseSystemUnits", True)
        measured = {"volume": float(self.get(properties, "Volume")), "area": float(self.get(properties, "SurfaceArea")), "com": [float(value) for value in self.get(properties, "CenterOfMass")]}
        area, perimeter, center = planar_properties(case)
        depth = case["depth_mm"] / 1000
        utility = self.get(self.app, "GetMathUtility")
        inverse = self.get(self.get(self.sketch, "ModelToSketchTransform"), "Inverse")
        def world(point):
            value = self.get(utility, "CreatePoint", self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_R8, point))
            return [float(item) for item in self.get(self.get(value, "MultiplyTransform", inverse), "ArrayData")]
        origin, normal_point = world([0.0, 0.0, 0.0]), world([0.0, 0.0, 1.0])
        normal = [normal_point[index] - origin[index] for index in range(3)]
        scale = math.sqrt(sum(value * value for value in normal))
        require(scale > 0, "sketch transform has no normal")
        base = world([center[0], center[1], 0.0])
        sign = -1 if case["reverse"] else 1
        expected_com = [base[index] + sign * normal[index] / scale * depth / 2 for index in range(3)]
        self.rec.close_number("volume", measured["volume"], area * depth, absolute=1e-22)
        self.rec.close_number("surface area", measured["area"], 2 * area + perimeter * depth, absolute=1e-18)
        for index in range(3):
            self.rec.close_number(f"center of mass {index}", measured["com"][index], expected_com[index], absolute=1e-9)
        snapshot.update(
            relations=relations,
            extrusion=extrusion,
            bodies=len(body_objects),
            mass=measured,
            expected_com=expected_com,
            feature_tree=self.feature_tree(),
            body_boxes=[
                safe_result(self.get(body, "GetBodyBox")) for body in body_objects
            ],
        )
        self.rec.flush()
        return snapshot


def run_worker(job_path, record_path):
    import Swapp
    from OracleIdentity import application_identity

    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    rec = Recorder(record_path, job)
    session, author, watchdog, preference, owned_pid = None, None, None, None, None
    try:
        require(job["phase"] in ("author", "verify"), "unknown native phase")
        require(tool_hashes() == job["tool_hashes"], "staged authoring tools changed before the native phase")
        require(not application_pids(), "an existing SOLIDWORKS process prevents a fresh owner-controlled case")
        session = rec.call("launch .34 COM", Swapp.Sw)
        identity = rec.call("OracleIdentity.application_identity", application_identity, session.app)
        rec.data["identity"] = identity
        rec.flush()
        owned_pid = identity["process_id"]
        require(identity["version_matches"] and identity["file_version_words"] == job["oracle"]["file_version_words"], "oracle executable version is not exactly 34.5.2.0604")
        require(identity["sha256"] == job["oracle"]["executable_sha256"] and identity["pe_machine"] == "0x8664", "oracle executable hash or architecture differs from the locked installation")
        require(session.revision == "34.5.2", "COM revision differs from the required oracle")
        watchdog = Swapp.Dismisser()
        watchdog.__enter__()
        preference = bool(rec.call("GetUserPreferenceToggle", session.app.GetUserPreferenceToggle, 10))
        rec.data["input_dimension_preference"] = {"before": preference, "restored": False}
        rec.flush()
        rec.call("SetUserPreferenceToggle", session.app.SetUserPreferenceToggle, 10, False)
        require(not bool(rec.call("read disabled input dimension preference", session.app.GetUserPreferenceToggle, 10)), "could not disable dimension prompt")
        author = CurveAuthor(session.app, rec, Swapp)
        case = job["case"]
        path = Path(job["native_path"])
        if job["phase"] == "author":
            author.build(case, session)
            author.snapshot(case, "authored")
            saved = rec.call("SaveAs3", session.save_as, author.model, path, parameters={"path": str(path), "version": 0, "options": 1})
            require(saved == (True, 0, 0), f"native save failed or warned: {saved}")
            author.refresh_dimension_names()
        else:
            require(path.is_file() and digest(path) == job["source_sha256"], "saved source hash differs before fresh-process verification")
            author.load_relation_bindings(case, job.get("requested_relations"))
            model, errors, warnings = rec.call("OpenDoc6", session.open, path, parameters={"path": str(path), "document_type": 1, "options": 1, "configuration": "", "errors": "out i4", "warnings": "out i4"})
            require(model is not None and errors == warnings == 0, f"saved source open failed or warned: {errors}, {warnings}")
            author.model = model
            author.snapshot(case, "reopened")
            dimensions = job["dimensions"]
            for item in dimensions:
                dimension = author.get(model, "Parameter", item["name"])
                require(dimension is not None, f"saved driving dimension is missing: {item['name']}")
                require(int(author.get(dimension, "DrivenState")) == 2 and not bool(author.get(dimension, "ReadOnly")), "saved dimension is not editable and driving")
                rec.close_number(item["name"], author.get(dimension, "SystemValue"), item["value"])
            selected = [item for item in dimensions if item["role"] == case["edit"]["target"]]
            require(len(selected) == 1, "requested dimension edit is missing or ambiguous")
            item = selected[0]
            dimension = author.get(model, "Parameter", item["name"])
            target = item["value"] * case["edit"]["factor"]
            status = int(author.get(dimension, "SetSystemValue3", target, 1, Swapp.nothing()))
            require(status == 0, f"driving dimension edit failed with status {status}")
            rec.close_number("edited driving dimension", author.get(dimension, "SystemValue"), target)
            author.snapshot(edited_case(case), "edited")
            rec.data["edit"] = {"name": item["name"], "before": item["value"], "after": target, "setter_status": status}
        rec.data["work_completed"] = True
    except Exception as error:
        rec.failure(error)
    finally:
        if author is not None and author.model is not None:
            try:
                title = rec.call("GetTitle", Swapp.cv, author.model, "GetTitle", parameters=[])
                rec.call("CloseDoc without saving edits", session.app.CloseDoc, str(title))
                author.model = None
            except Exception as error:
                rec.failure(error, cleanup=True)
        if session is not None and preference is not None:
            try:
                rec.call("restore input dimension preference", session.app.SetUserPreferenceToggle, 10, preference)
                actual = bool(rec.call("read restored input dimension preference", session.app.GetUserPreferenceToggle, 10))
                require(actual == preference, "input dimension preference was not restored")
                rec.data["input_dimension_preference"]["restored"] = True
            except Exception as error:
                rec.failure(error, cleanup=True)
        if session is not None:
            try:
                rec.call("ExitApp", session.close)
                require(not session.diagnostics, f"oracle session cleanup diagnostics: {session.diagnostics}")
                require(owned_pid is not None and wait_exit(owned_pid), "owned SOLIDWORKS process did not exit")
            except Exception as error:
                rec.failure(error, cleanup=True)
        if watchdog is not None:
            watchdog.__exit__(None, None, None)
            rec.data.update(dialogs=watchdog.log, progress_windows=watchdog.progress)
            if watchdog.log:
                rec.failure(EvidenceFailure("a native dialog was dismissed or the watchdog failed"), cleanup=True)
        if job["phase"] == "verify" and Path(job["native_path"]).is_file():
            rec.data["source_sha256_after"] = digest(job["native_path"])
            if rec.data["source_sha256_after"] != job["source_sha256"]:
                rec.failure(EvidenceFailure("verification or dimension edit modified the original source file"), cleanup=True)
        rec.data.update(passed=bool(rec.data.get("work_completed")) and rec.data["first_failure"] is None, finished_at=time.time())
        rec.flush()
    return 0 if rec.data["passed"] else 2


def cleanup_owned_process(identity, oracle):
    from win32api import OpenProcess, TerminateProcess
    from win32event import WAIT_OBJECT_0, WAIT_TIMEOUT, WaitForSingleObject
    from OracleIdentity import process_creation_time

    pid, created = identity.get("process_id"), identity.get("process_creation_filetime")
    result = {"pid": pid, "expected_creation_filetime": created, "terminated": False}
    require(type(pid) is int and pid > 0 and type(created) is int and created > 0, "owned cleanup requires an exact process creation identity")
    require(identity.get("version_matches") and identity.get("sha256") == oracle["executable_sha256"], "owned cleanup requires the pinned oracle identity")
    if pid not in application_pids():
        result["application_absent"] = True
        return result
    handle = OpenProcess(0x00101001, False, pid)
    try:
        result["actual_creation_filetime"] = process_creation_time(handle)
        require(result["actual_creation_filetime"] == created, "recorded PID now belongs to a different process; cleanup refused")
        state = WaitForSingleObject(handle, 0)
        require(state in (WAIT_OBJECT_0, WAIT_TIMEOUT), "owned process lifetime state is unavailable")
        if state == WAIT_TIMEOUT:
            TerminateProcess(handle, 1)
            result["terminated"] = True
        result["exit_confirmed"] = WaitForSingleObject(handle, 30000) == WAIT_OBJECT_0
        require(result["exit_confirmed"], "owned SOLIDWORKS process did not exit after termination")
    finally:
        handle.Close()
    return result


def dispatch_job(directory, job, timeout):
    directory.mkdir(parents=True, exist_ok=False)
    job_path, record_path = directory / "Job.json", directory / "Record.json"
    write_json(job_path, job)
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", str(job_path), str(record_path)]
    started = time.monotonic()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        stdout, stderr, exit_code = completed.stdout, completed.stderr, completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, exit_code, timed_out = str(error.stdout or ""), str(error.stderr or ""), None, True
    (directory / "Stdout.txt").write_text(stdout, encoding="utf-8")
    (directory / "Stderr.txt").write_text(stderr, encoding="utf-8")
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else {"first_failure": None, "passed": False}
    record.update(worker_exit_code=exit_code, worker_timed_out=timed_out, worker_seconds=time.monotonic() - started)
    if timed_out or exit_code != 0:
        if record.get("first_failure") is None:
            record["first_failure"] = {"stage": record.get("stage", "worker-start"), "type": "WorkerFailure", "error": "worker timed out" if timed_out else f"worker exited {exit_code}"}
        record["passed"] = False
        identity = record.get("identity", {})
        if identity.get("process_id"):
            try:
                record["forced_owned_process_cleanup"] = cleanup_owned_process(identity, job["oracle"])
            except Exception as error:
                record.setdefault("cleanup_errors", []).append({"stage": "forced-owned-process-cleanup", "type": type(error).__name__, "error": str(error)})
    write_json(record_path, record)
    return record


def author_case(root, case, oracle, timeout, hashes):
    directory = root / ("Heldout" if case["split"] == "heldout" else "Discovery" if case["split"] == "discovery" else "Controls") / case["name"]
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / (case["name"] + ".SLDPRT")
    record = {"case": case, "native_path": str(path), "passed": False}
    job = {"case": case, "oracle": oracle, "phase": "author", "native_path": str(path), "tool_hashes": hashes}
    record["author"] = dispatch_job(directory / "Author", job, timeout)
    if record["author"].get("passed"):
        require(path.is_file(), "successful authoring did not produce its native file")
        record["sha256"] = digest(path)
        job.update(phase="verify", source_sha256=record["sha256"], dimensions=record["author"]["dimensions"], requested_relations=record["author"]["requested_relations"])
        record["verify"] = dispatch_job(directory / "Verify", job, timeout)
        record["passed"] = record["verify"].get("passed", False)
    write_json(directory / "Manifest.json", record)
    return record


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        return run_worker(sys.argv[2], sys.argv[3])
    parser = argparse.ArgumentParser(description="Owner-controlled 2026 curve source authoring; never a native-format writer")
    parser.add_argument("specs", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--checkout-root", type=Path, required=True)
    parser.add_argument("--generator-revision", required=True)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--timeout", type=float, default=240)
    args = parser.parse_args()
    source, output, checkout = args.specs.resolve(), args.output.resolve(), args.checkout_root.resolve()
    require(source.is_file() and (checkout / "AGENTS.md").is_file(), "specification or repository checkout root does not exist")
    require(not output.is_relative_to(checkout), "native sources and measurements must stay outside the checkout")
    require(not output.exists(), "use a new output directory so prior locks and evidence cannot be overwritten")
    require(args.timeout > 0, "worker timeout must be positive")
    spec = json.loads(source.read_text(encoding="utf-8"))
    require(spec["schema"] == "kit-sw2026-curve-source-specs/1", "unknown curve source specification")
    cases, controls = spec["cases"], spec["controls"]
    names = [case["name"] for case in cases + controls]
    require(len(set(names)) == len(names) and all(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", name) for name in names), "case names must be unique safe path components")
    require(sum(case["split"] == "discovery" for case in cases) == 24 and sum(case["split"] == "heldout" for case in cases) == 6 and len(controls) == 2, "family requires 24 discovery, 6 heldout and 2 independent controls")
    require(all(case["split"] == "control" for case in controls), "control split is invalid")
    require(set(args.case) <= {case["name"] for case in cases}, "requested case is not in the neutral specification")
    selected = [case for case in cases if not args.case or case["name"] in args.case]
    require(not application_pids(), "the oracle owner must close existing SOLIDWORKS sessions before this batch")
    hashes = tool_hashes()
    output.mkdir(parents=True)
    write_json(output / "Specs.json", spec)
    batch = {"schema": "kit-sw2026-curve-source-batch/1", "generator_revision": args.generator_revision, "script_sha256": digest(__file__), "tool_hashes": hashes, "specs_sha256": digest(source), "oracle": spec["oracle"], "started_at": time.time(), "controls_before": [], "cases": [], "controls_after": [], "pending_cases": [], "first_failure": None, "locked": False}
    def checkpoint():
        write_json(output / "Batch.json", batch)
    def failed(record):
        if not record.get("passed") and batch["first_failure"] is None:
            batch["first_failure"] = {"case": record["case"]["name"], "phase": "author" if not record["author"].get("passed") else "verify", "failure": record["author"].get("first_failure") or record.get("verify", {}).get("first_failure")}
    checkpoint()
    try:
        for control in controls:
            record = author_case(output, control, spec["oracle"], args.timeout, hashes)
            batch["controls_before"].append(record)
            failed(record)
            checkpoint()
        for case in selected:
            if batch["first_failure"] is not None:
                batch["pending_cases"].append(case["name"])
                checkpoint()
                continue
            record = author_case(output, case, spec["oracle"], args.timeout, hashes)
            batch["cases"].append(record)
            failed(record)
            checkpoint()
    except Exception as error:
        if batch["first_failure"] is None:
            batch["first_failure"] = {"stage": "controller", "type": type(error).__name__, "error": repr(error), "traceback": traceback.format_exc()}
    finally:
        for record in batch["controls_before"]:
            if not record.get("passed"):
                continue
            job = {"case": record["case"], "oracle": spec["oracle"], "phase": "verify", "native_path": record["native_path"], "source_sha256": record["sha256"], "dimensions": record["author"]["dimensions"], "requested_relations": record["author"]["requested_relations"], "tool_hashes": hashes}
            try:
                after = dispatch_job(output / "ControlsAfter" / record["case"]["name"], job, args.timeout)
                batch["controls_after"].append({"case": record["case"]["name"], "passed": after.get("passed", False), "record": after})
                if not after.get("passed") and batch["first_failure"] is None:
                    batch["first_failure"] = {"case": record["case"]["name"], "phase": "control-after", "failure": after.get("first_failure")}
            except Exception as error:
                batch["controls_after"].append({"case": record["case"]["name"], "passed": False, "error": repr(error)})
                if batch["first_failure"] is None:
                    batch["first_failure"] = {"stage": "control-after", "error": repr(error)}
            checkpoint()
    completed_names = {record["case"]["name"] for record in batch["cases"]}
    batch["pending_cases"] = [case["name"] for case in selected if case["name"] not in completed_names]
    if tool_hashes() != hashes or digest(source) != batch["specs_sha256"]:
        if batch["first_failure"] is None:
            batch["first_failure"] = {"stage": "lock", "error": "authoring tools or neutral specifications changed during the batch"}
    complete = len(selected) == 30 and len(batch["cases"]) == 30 and not batch["pending_cases"]
    healthy = len(batch["controls_before"]) == len(batch["controls_after"]) == 2 and all(record["passed"] for record in batch["controls_before"] + batch["controls_after"])
    eligible = complete and healthy and batch["first_failure"] is None and all(record["passed"] for record in batch["cases"])
    locked_cases = []
    if eligible:
        try:
            for record in batch["cases"] + batch["controls_before"]:
                require(digest(record["native_path"]) == record["sha256"], "native source changed after its checks")
                locked_cases.append({"name": record["case"]["name"], "split": record["case"]["split"], "sha256": record["sha256"], "file": str(Path(record["native_path"]).relative_to(output)), "manifest_sha256": digest(Path(record["native_path"]).parent / "Manifest.json")})
        except Exception as error:
            eligible = False
            batch["first_failure"] = {"stage": "lock", "type": type(error).__name__, "error": repr(error)}
    if eligible:
        batch.update(locked=True, finished_at=time.time())
        checkpoint()
        lock = {"schema": "kit-sw2026-curve-source-lock/1", "created_at": time.time(), "generator_revision": args.generator_revision, "script_sha256": batch["script_sha256"], "tool_hashes": hashes, "specs_sha256": batch["specs_sha256"], "batch_sha256": digest(output / "Batch.json"), "oracle": spec["oracle"], "cases": locked_cases, "writer_implementation_started": False, "heldout_policy": "Heldout native files and streams must not be inspected while deriving or implementing the family; only independent heldout oracle results establish generalization", "acceptance_scope": "2026-authored source corpus only; no Kit-written curve output or writer acceptance is established"}
        write_json(output / "Lock.json", lock)
    else:
        batch.update(finished_at=time.time(), incomplete_selection=not complete, controls_healthy=healthy)
        checkpoint()
    print(json.dumps({"locked": batch["locked"], "passed_cases": sum(record["passed"] for record in batch["cases"]), "selected_cases": len(selected), "first_failure": batch["first_failure"], "pending_cases": batch["pending_cases"]}))
    return 0 if batch["locked"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
