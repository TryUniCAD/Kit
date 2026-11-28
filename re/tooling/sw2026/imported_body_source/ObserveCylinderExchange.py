from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import json
from math import dist, isclose, isfinite, sqrt, tau
import os
from pathlib import Path, PureWindowsPath
import re
from time import time

from AuthorCurves import Recorder, digest, require, write_json
from AuthorImportedBody import (
    IMPORTED,
    OBJECT_SAME,
    SHEET,
    SOLID,
    ImportedBodyAuthor,
    cylinder_expectation,
)
from AuthorRectangleAnchors import CONTROL, ORACLE, control
from ObserveKernelBodyRestore import expected_box
from ObserveKernelExchange import phase as exchange_phase
from RunImportedBodySources import VERSION, cases as native_cases, oracle_identity

SCHEMA = "kit.sw2026.local-cylinder-exchange.v1"
BUILD_RECEIPT = "92fcf0ba4589e92aa3967e9341aff655e7df442748f002d5e1c7dc6727ea7ff3"
NATIVE_RECEIPT = "bbaa59c9661882912fdc0f140feb864824a9ddc36609e902e359d8c50ffd1105"
STOCK = {
    "CylinderZ": (
        "ef72c75f230331903726a4e48ca61682736289dba78261d654071f2fe2a54166",
        "d6e924671f7e65f9d985f9043cb0c03ac5ecd258eae08d732c0b038f3363e09d",
    ),
    "CylinderReverseY": (
        "91a3a675d932d0f14c886446885980d484beb66a4f821d5ecfe9908e41182179",
        "81b3209741cffe06e5332b552d82743554eb9ce3415688b82e3c32f78cda623f",
    ),
}
GENERATED = {
    "TranslatedZ": "20f764878d7ef568f01a9df61b276522f71a16aa7b13e2a2e121fd6ebf410b44",
    "ReverseY": "85c47d7beb3b2c4a9e01d98341197e62f345601fcc4e813afb976cccc2b79852",
}
TOOL_NAMES = frozenset(
    (
        "AuthorCurves.py",
        "AuthorImportedBody.py",
        "AuthorRectangleAnchors.py",
        "InspectFresh.py",
        "ObserveCylinderExchange.py",
        "ObserveKernelBodyRestore.py",
        "ObserveKernelExchange.py",
        "OracleIdentity.py",
        "RunImportedBodySources.py",
        "Swapp.py",
    )
)
BEFORE = ("ApplicationBefore", "ExportBefore", "SourceZ", "StockZ")
AFTER = ("StockReverseY", "SourceReverseY", "ExportAfter", "ApplicationAfter")
PHASES = (*BEFORE, *GENERATED, *AFTER)
TOLERANCES = {
    "relative_mass": 2e-7,
    "volume_m3": 1e-22,
    "area_m2": 1e-18,
    "position_m": 1e-10,
    "direction": 1e-9,
    "period_rad": 1e-9,
}
MAX_FILE_BYTES = 64 * 1024**2


def known_cases():
    source_models = native_cases("topology")
    return {
        "StockZ": {
            "role": "native_raw_control",
            "source": "CylinderZ",
            "sha256": STOCK["CylinderZ"][1],
            "size": 3525,
            "model": source_models["CylinderZ"],
        },
        "StockReverseY": {
            "role": "native_raw_control",
            "source": "CylinderReverseY",
            "sha256": STOCK["CylinderReverseY"][1],
            "size": 3525,
            "model": source_models["CylinderReverseY"],
        },
        "TranslatedZ": {
            "role": "generated_disclosed",
            "sha256": GENERATED["TranslatedZ"],
            "size": 1414,
            "model": {
                "face_center_m": (0.01625, -0.0085, 0.003375),
                "axis": (0.0, 0.0, 1.0),
                "radius_m": 0.00675,
                "height_m": 0.017125,
            },
        },
        "ReverseY": {
            "role": "generated_disclosed",
            "sha256": GENERATED["ReverseY"],
            "size": 1414,
            "model": {
                "face_center_m": (-0.011125, 0.0285, -0.004875),
                "axis": (0.0, -1.0, 0.0),
                "radius_m": 0.004625,
                "height_m": 0.02425,
            },
        },
    }


def raw_bytes(path, size=None):
    require(
        path.is_file() and not path.is_symlink(),
        f"expected a regular packet file: {path.name}",
    )
    length = path.stat().st_size
    require(
        0 < length <= MAX_FILE_BYTES and (size is None or length == size),
        f"packet length differs: {path.name}",
    )
    content = path.read_bytes()
    require(len(content) == length, f"packet length changed while reading: {path.name}")
    return content


def checked(path, checksum, size=None):
    require(
        type(checksum) is str and re.fullmatch(r"[0-9a-f]{64}", checksum),
        f"invalid packet digest: {path.name}",
    )
    content = raw_bytes(path, size)
    require(
        sha256(content).hexdigest() == checksum, f"packet hash differs: {path.name}"
    )
    return content


def unique_object(rows):
    values = {}
    for name, value in rows:
        require(name not in values, f"duplicate cylinder packet key: {name}")
        values[name] = value
    return values


def guest_directory(value):
    require(
        type(value) is str and re.fullmatch(r"C:\\KitCylinderExchange[0-9]{2}", value),
        "use a new C:\\KitCylinderExchangeNN guest-local directory",
    )
    return PureWindowsPath(value)


def source_receipt(content):
    receipt = json.loads(content, object_pairs_hook=unique_object)
    require(
        receipt["cohort"] == "topology"
        and receipt["oracle_version"] == VERSION
        and receipt["oracle_sha256"] == ORACLE
        and receipt["passed"] is True
        and receipt["controls_healthy"] is True
        and receipt["distinct_processes"] == 6
        and receipt["writer_outputs"] == 0
        and set(receipt["sources"]) == STOCK.keys(),
        "disclosed native source evidence differs",
    )
    for name, (source_hash, _) in STOCK.items():
        source = receipt["sources"][name]
        require(
            source["source_sha256"] == source_hash
            and source["observed"]["feature"]
            == {"native_id": 26, "name": "Imported1", "type": IMPORTED}
            and source["observed"]["topology"]
            == {
                "vertices": 0,
                "edges": 2,
                "faces": 3,
                "planar_faces": 2,
                "cylindrical_faces": 1,
            },
            f"disclosed native source identity differs: {name}",
        )
    return receipt


def case_bytes(root, name, case):
    require(name in known_cases(), "unexpected cylinder raw case")
    return checked(root / (name + ".x_b"), case["sha256"], case["size"])


def verify_job(path, checksum):
    require(path.name == "Job.json", "use the exact cylinder Job.json locator")
    content = checked(path, checksum)
    root = path.parent
    tools = root / "Tools"
    require(
        tools.is_dir()
        and not tools.is_symlink()
        and Path(__file__).resolve().parent == tools,
        "run the frozen cylinder observer in the packet's Tools directory",
    )
    job = json.loads(content, object_pairs_hook=unique_object)
    require(
        set(job)
        == {
            "schema",
            "oracle_version",
            "oracle_sha256",
            "tool_checkout_head",
            "guest_directory",
            "control_sha256",
            "build_sha256",
            "source_receipt_sha256",
            "tools_sha256",
            "cases",
            "phases",
            "tolerances",
        }
        and job["schema"] == SCHEMA
        and job["oracle_version"] == VERSION
        and job["oracle_sha256"] == ORACLE
        and type(job["tool_checkout_head"]) is str
        and re.fullmatch(r"[0-9a-f]{40}", job["tool_checkout_head"])
        and job["control_sha256"] == CONTROL
        and job["build_sha256"] == BUILD_RECEIPT
        and job["source_receipt_sha256"] == NATIVE_RECEIPT
        and job["phases"] == list(PHASES)
        and job["tolerances"] == TOLERANCES
        and job["cases"] == json.loads(json.dumps(known_cases())),
        "exact cylinder job specification changed",
    )
    guest_directory(job["guest_directory"])
    require(
        set(job["tools_sha256"]) == TOOL_NAMES,
        "unexpected cylinder oracle tool inventory",
    )
    for name, identity in job["tools_sha256"].items():
        checked(tools / name, identity)
    checked(root / "Control.SLDPRT", CONTROL)
    checked(root / "Build.json", BUILD_RECEIPT)
    source_receipt(checked(root / "NativeSources.json", NATIVE_RECEIPT))
    require(
        {path.name for path in root.iterdir() if path.suffix.casefold() == ".x_b"}
        == {name + ".x_b" for name in known_cases()},
        "cylinder raw case inventory differs",
    )
    for name, (source_hash, _) in STOCK.items():
        checked(root / (name + ".SLDPRT"), source_hash)
    for name, case in job["cases"].items():
        case_bytes(root, name, case)
    return job


def number(observer, label, actual, expected, tolerance, *, relative=0.0):
    actual, expected = float(actual), float(expected)
    passed = isfinite(actual) and isclose(
        actual, expected, rel_tol=relative, abs_tol=tolerance
    )
    observer.rec.data["checks"].append(
        {
            "name": label,
            "actual": actual,
            "expected": expected,
            "passed": passed,
            "absolute_tolerance": tolerance,
            "relative_tolerance": relative,
        }
    )
    observer.rec.flush()
    require(passed, f"{label}: {actual!r} differs from {expected!r}")


def vector(observer, label, actual, expected, tolerance):
    require(len(actual) == len(expected) == 3, f"{label} is not a spatial triple")
    for axis, (got, want) in enumerate(zip(actual, expected, strict=True)):
        number(observer, f"{label} coordinate {axis}", got, want, tolerance)


def numeric_values(values, length, label):
    result = tuple(float(value) for value in values)
    require(len(result) == length and all(map(isfinite, result)), f"invalid {label}")
    return result


def dot(left, right):
    return sum(a * b for a, b in zip(left, right, strict=True))


def expected_geometry(model):
    start, axis, radius, height = (
        model[key] for key in ("face_center_m", "axis", "radius_m", "height_m")
    )
    end = tuple(a + b * height for a, b in zip(start, axis, strict=True))
    radial = tuple(radius * sqrt(max(0.0, 1.0 - value**2)) for value in axis)
    extents = tuple(zip(start, end, radial, strict=True))
    bounds = (
        tuple(min(a, b) - r for a, b, r in extents),
        tuple(max(a, b) + r for a, b, r in extents),
    )
    return (start, end), bounds, cylinder_expectation(model)


def measure_extrema(observer, body, expected):
    observed = [[], []]
    for axis in range(3):
        for index, sign in enumerate((-1.0, 1.0)):
            direction = [0.0, 0.0, 0.0]
            direction[axis] = sign
            pythoncom = observer.sw.pythoncom
            values = [
                observer.sw.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_R8, 0.0)
                for _ in range(3)
            ]
            answer = observer.get(body, "GetExtremePoint", *direction, *values)
            if isinstance(answer, tuple):
                require(
                    len(answer) == 4 and bool(answer[0]),
                    "typed extreme point did not report success and XYZ",
                )
                point = numeric_values(answer[1:], 3, "extreme point")
            else:
                require(bool(answer), "native extreme point was unavailable")
                point = numeric_values(
                    (item.value for item in values), 3, "extreme point"
                )
            number(
                observer,
                f"bound axis {axis} sign {sign}",
                point[axis],
                expected[index][axis],
                TOLERANCES["position_m"],
            )
            observed[index].append(point[axis])
    return observed


def measure_circle(observer, edge, centers, axis, radius):
    curve = observer.typed(observer.get(edge, "GetCurve"), "Curve")
    require(
        bool(observer.get(curve, "IsCircle")),
        "periodic rim lacks an analytic circular carrier",
    )
    xyz = numeric_values(observer.get(curve, "CircleParams"), 7, "circle parameters")
    end = min(range(2), key=lambda index: dist(xyz[:3], centers[index]))
    vector(observer, "rim center", xyz[:3], centers[end], TOLERANCES["position_m"])
    number(
        observer,
        "rim normal alignment",
        abs(dot(xyz[3:6], axis)),
        1.0,
        TOLERANCES["direction"],
    )
    number(observer, "rim radius", xyz[6], radius, TOLERANCES["position_m"])
    trim = observer.typed(observer.get(edge, "GetCurveParams3"), "CurveParamData")
    start = float(observer.get(trim, "UMinValue"))
    finish = float(observer.get(trim, "UMaxValue"))
    number(observer, "rim period", abs(finish - start), tau, TOLERANCES["period_rad"])
    return end, {
        "center_m": xyz[:3],
        "normal": xyz[3:6],
        "radius_m": xyz[6],
        "trim": (start, finish),
    }


def loop_rims(observer, face, edges, count):
    loops = tuple(observer.get(face, "GetLoops") or ())
    require(
        int(observer.get(face, "GetLoopCount")) == len(loops) == count,
        "periodic cylinder face loop inventory differs",
    )
    result = []
    for value in loops:
        loop = observer.typed(value, "Loop2")
        rim = tuple(observer.get(loop, "GetEdges") or ())
        require(len(rim) == 1, "cylinder ring does not own exactly one edge")
        matches = [
            end
            for end, edge in edges.items()
            if int(observer.get(observer.app, "IsSame", rim[0], edge)) == OBJECT_SAME
        ]
        require(len(matches) == 1, "cylinder loop lacks its actual body rim")
        result.extend(matches)
    return tuple(sorted(result))


def measure_faces(observer, body, edges, centers, axis, radius):
    caps, mantles = {}, []
    for value in observer.get(body, "GetFaces") or ():
        face = observer.typed(value, "Face2")
        observer.exact_object(
            observer.get(face, "GetBody"), body, "face's actual cylinder body"
        )
        surface = observer.typed(observer.get(face, "GetSurface"), "Surface")
        if bool(observer.get(surface, "IsPlane")):
            (end,) = loop_rims(observer, face, edges, 1)
            require(end not in caps, "both cap faces attach to the same rim")
            plane = numeric_values(
                observer.get(surface, "PlaneParams"), 6, "cap plane parameters"
            )
            normal = numeric_values(
                observer.get(face, "Normal"), 3, "outward cap normal"
            )
            expected_normal = axis if end else tuple(-value for value in axis)
            vector(
                observer,
                "cap outward normal",
                normal,
                expected_normal,
                TOLERANCES["direction"],
            )
            number(
                observer,
                "cap plane normal alignment",
                abs(dot(plane[:3], axis)),
                1.0,
                TOLERANCES["direction"],
            )
            offset = tuple(a - b for a, b in zip(plane[3:], centers[end], strict=True))
            number(
                observer,
                "cap plane station",
                dot(offset, axis),
                0.0,
                TOLERANCES["position_m"],
            )
            caps[end] = {
                "outward_normal": normal,
                "plane_parameters": plane,
                "rim_station": end,
            }
        else:
            require(
                bool(observer.get(surface, "IsCylinder"))
                and loop_rims(observer, face, edges, 2) == (0, 1),
                "cylinder mantle must own both distinct cap rims",
            )
            wall = numeric_values(
                observer.get(surface, "CylinderParams"), 7, "mantle cylinder parameters"
            )
            number(
                observer,
                "mantle axis alignment",
                abs(dot(wall[3:6], axis)),
                1.0,
                TOLERANCES["direction"],
            )
            number(observer, "mantle radius", wall[6], radius, TOLERANCES["position_m"])
            offset = tuple(a - b for a, b in zip(wall[:3], centers[0], strict=True))
            along = dot(offset, axis)
            vector(
                observer,
                "mantle transverse axis position",
                offset,
                tuple(along * value for value in axis),
                TOLERANCES["position_m"],
            )
            mantles.append(wall)
    require(
        set(caps) == {0, 1} and len(mantles) == 1,
        "isolated cylinder must have two caps and one mantle",
    )
    return [caps[0], caps[1]], mantles[0]


def measure_cylinder(observer, expected):
    model = expected["model"]
    centers, bounds, mass_target = expected_geometry(model)
    part = observer.typed(observer.model, "PartDoc")
    solids = tuple(observer.get(part, "GetBodies2", SOLID, False) or ())
    require(
        len(solids) == 1 and not observer.get(part, "GetBodies2", SHEET, False),
        "cylinder must expose one solid and zero sheet bodies",
    )
    body = observer.typed(solids[0], "Body2")
    require(
        int(observer.get(body, "GetType")) == SOLID
        and not bool(observer.get(body, "IsTemporaryBody"))
        and not observer.get(body, "GetVertices"),
        "imported periodic body must have zero native vertices",
    )
    raw_edges = tuple(observer.get(body, "GetEdges") or ())
    require(len(raw_edges) == 2, "periodic cylinder must have exactly two edges")
    edges, circles = {}, {}
    axis, radius = model["axis"], model["radius_m"]
    for item in raw_edges:
        edge = observer.typed(item, "Edge")
        end, circle = measure_circle(observer, edge, centers, axis, radius)
        require(end not in edges, "periodic edges attach to the same cap station")
        edges[end], circles[end] = edge, circle
    caps, mantle = measure_faces(observer, body, edges, centers, axis, radius)
    actual_bounds = measure_extrema(observer, body, bounds)
    mass = numeric_values(
        observer.get(body, "GetMassProperties", 1.0), 12, "body mass properties"
    )
    vector(
        observer,
        "body center of mass",
        mass[:3],
        mass_target["com"],
        TOLERANCES["position_m"],
    )
    for name, value, units_key in (
        ("volume", mass[3], "volume_m3"),
        ("area", mass[4], "area_m2"),
    ):
        number(
            observer,
            name,
            value,
            mass_target[name],
            TOLERANCES[units_key],
            relative=TOLERANCES["relative_mass"],
        )
    require(
        int(
            observer.get(
                observer.get(observer.model, "Extension"), "GetWhatsWrongCount"
            )
        )
        == 0,
        "observed cylinder document has native diagnostics",
    )
    return {
        "solids": 1,
        "vertices": 0,
        "edges": len(edges),
        "faces": len(caps) + 1,
        "cap_rims": [circles[0], circles[1]],
        "caps": caps,
        "mantle_parameters": mantle,
        "extreme_bounds_m": actual_bounds,
        "com_m": mass[:3],
        "volume_m3": mass[3],
        "area_m2": mass[4],
    }


def stock_snapshot(observer, case):
    native = observer.get(observer.model, "FeatureByName", "Imported1")
    require(native is not None, "stock native source lost its actual import owner")
    feature = observer.typed(native, "Feature")
    observed = observer.observe(feature, case["model"] | {"feature_name": "Imported1"})
    require(
        observed["feature"] == {"native_id": 26, "name": "Imported1", "type": IMPORTED},
        "stock cylinder feature identity differs",
    )
    return {
        "feature": observed["feature"],
        "tree": observed["tree"],
        "geometry": measure_cylinder(observer, case),
    }


def stock_phase(directory, label, path, case):
    import Swapp
    from OracleIdentity import application_identity

    source_hash = STOCK[case["source"]][0]
    checked(path, source_hash)
    rec = Recorder(
        directory / (label + ".json"), {"case": label, "source_sha256": source_hash}
    )
    result = {"passed": False, "source_sha256": source_hash}
    controller, observer = None, None
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("verify idle oracle", Swapp.sweep)
            controller = rec.call(
                "launch fresh native cylinder source oracle", Swapp.Sw
            )
            require(
                controller.revision == Swapp.EXPECTED_BUILD,
                "stock COM revision differs",
            )
            result["oracle_identity"] = oracle_identity(
                rec.call(
                    "bind exact source oracle", application_identity, controller.app
                )
            )
            observer = ImportedBodyAuthor(controller.app, rec, Swapp)
            observer.model, error, warning = rec.call(
                "open exact stock cylinder read-only",
                controller.open,
                path,
                read_only=True,
            )
            result.update(open_errors=error, open_warnings=warning)
            require(
                observer.model is not None
                and error == warning == 0
                and Path(observer.get(observer.model, "GetPathName")).samefile(path),
                "stock cylinder did not open cleanly",
            )
            result["cold"] = stock_snapshot(observer, case)
            observer.rebuild()
            result["rebuilt"] = stock_snapshot(observer, case)
            require(
                result["cold"]["tree"] == result["rebuilt"]["tree"],
                "stock source tree changed on rebuild",
            )
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if controller is not None:
                try:
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
    try:
        checked(path, source_hash)
    except Exception as error:
        rec.failure(error)
    result.update(
        dialogs=dialogs.log,
        progress_windows=dialogs.progress,
        numeric_checks=len(rec.data["checks"]),
        first_failure=rec.data["first_failure"],
    )
    result["passed"] = bool(
        result["passed"]
        and not dialogs.log
        and not result.get("controller_diagnostics")
        and not rec.data["first_failure"]
        and not rec.data["cleanup_errors"]
    )
    rec.data.update(result=result, passed=result["passed"], finished_at=time())
    rec.flush()
    return result | {"record_sha256": digest(rec.path)}


def stage_local(packet, directory, name, checksum):
    content = checked(packet / name, checksum)
    local = directory / name
    with local.open("xb") as stream:
        stream.write(content)
    checked(local, checksum, len(content))
    return local


def observe_phase(directory, packet, seed, job, name):
    if name in ("ApplicationBefore", "ApplicationAfter"):
        return "native_application_control", control(directory, name, seed)
    if name in ("ExportBefore", "ExportAfter"):
        return "native_binary_export_control", exchange_phase(
            directory, name, expected_box(), None, "exchange"
        )
    if name in ("SourceZ", "SourceReverseY"):
        case = job["cases"][name.replace("Source", "Stock", 1)]
        source = case["source"]
        path = stage_local(packet, directory, source + ".SLDPRT", STOCK[source][0])
        return "native_source_control", stock_phase(directory, name, path, case)
    case = job["cases"][name]
    raw = case_bytes(packet, name, case)
    return case["role"], exchange_phase(
        directory, name, case, raw, "exchange", observe_body=measure_cylinder
    )


def run(path, checksum, job):
    require(
        os.name == "nt",
        "native cylinder execution requires the root-owned Windows guest",
    )
    directory = Path(job["guest_directory"])
    packet = path.parent
    public = packet / "Result.json"
    require(
        not public.exists() and not public.is_symlink(),
        "cylinder exchange receipt already exists",
    )
    directory.mkdir()
    seed = stage_local(packet, directory, "Control.SLDPRT", CONTROL)
    receipt = {
        "schema": SCHEMA,
        "job_sha256": checksum,
        "oracle_sha256": ORACLE,
        "oracle_version": VERSION,
        "passed": False,
        "native_writer_outputs": 0,
        "heldout_cases": 0,
        "phases": [],
        "tools_sha256": job["tools_sha256"],
        "tolerances": TOLERANCES,
    }

    def record(name):
        receipt["stage"] = name
        write_json(public, receipt)
        try:
            role, observed = observe_phase(directory, packet, seed, job, name)
        except Exception as error:
            role, observed = "phase_error", {"passed": False, "failure": repr(error)}
        receipt["phases"].append({"name": name, "role": role, **observed})
        write_json(public, receipt)
        return observed["passed"]

    with (
        (directory / "Oracle.log").open("x", encoding="utf-8") as log,
        redirect_stdout(log),
        redirect_stderr(log),
    ):
        try:
            before_passed = all(record(name) for name in BEFORE)
            receipt["candidates_enabled"] = before_passed
            if before_passed:
                for name in GENERATED:
                    record(name)
        finally:
            for name in AFTER:
                record(name)
    results = {phase["name"]: phase for phase in receipt["phases"]}
    identities = {
        (identity["process_id"], identity["process_creation_filetime"])
        for phase in results.values()
        if (identity := phase.get("oracle_identity"))
    }
    controls = (*BEFORE, *AFTER)
    healthy_controls = [results.get(name, {}) for name in controls]
    control_identities = {
        (identity["process_id"], identity["process_creation_filetime"])
        for phase in healthy_controls
        if (identity := phase.get("oracle_identity"))
    }
    try:
        verify_job(path, checksum)
        checked(seed, CONTROL)
        receipt["packet_unchanged"] = True
    except Exception as error:
        receipt.update(packet_unchanged=False, packet_failure=repr(error))
    receipt.update(
        distinct_processes=len(identities),
        controls_healthy=len(control_identities) == len(controls)
        and all(row.get("passed") for row in healthy_controls),
    )
    receipt["passed"] = (
        receipt["packet_unchanged"]
        and receipt["controls_healthy"]
        and tuple(results) == PHASES
        and len(identities) == len(PHASES)
        and all(row["passed"] for row in results.values())
    )
    receipt["stage"] = "passed" if receipt["passed"] else "failed"
    write_json(public, receipt)
    print(
        json.dumps(
            {
                name: receipt[name]
                for name in (
                    "stage",
                    "passed",
                    "controls_healthy",
                    "distinct_processes",
                )
            }
        )
    )
    return 0 if receipt["passed"] else 3


def main():
    parser = ArgumentParser(
        description="Verify or measure the exact bare cylinder binary exchange packet"
    )
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        require(not args.job.is_symlink(), "use the regular cylinder packet job")
        path = args.job.resolve()
        job = verify_job(path, args.job_sha256)
        if args.verify_only:
            print(
                json.dumps(
                    {
                        "verified": True,
                        "job_sha256": args.job_sha256,
                        "native_processes": 0,
                    }
                )
            )
            return 0
        return run(path, args.job_sha256, job)
    except Exception as error:
        print(json.dumps({"stage": "refused", "failure": repr(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
