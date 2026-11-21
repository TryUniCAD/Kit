import argparse
import ctypes
from ctypes import wintypes
from collections import Counter
from hashlib import sha256
from importlib.machinery import ExtensionFileLoader
from importlib.util import find_spec
from io import BytesIO
from itertools import combinations, product
import json
from math import isclose, isfinite, prod
import os
from pathlib import Path
import sys
from time import time_ns
from xml.etree.ElementTree import fromstring
from zipfile import ZipFile


BUILD = "4fd3bf320d9566a27e60069fc8387448aaa3a094"
PYTHON_EXE = "b4ca526908e5c93250b851427fa3265936472f1148eb7781c685afa2a13fb996"
APP_MODULE = "e6d9c7609613c4f8247b8157386ea27adffa102b3e1f8c5b9b0b0e912e0bfde0"
APP_LIBRARY = "efe57703f688cfefe7a6d806e3ea8592ffce516b06874c58597ab7c460780921"
PART_MODULE = "3f99965d8bac7f0302041ad3760ba5a1c027ac60676dd1db642834d8fd22fb53"
PROGRAM_VERSION = "1.1R20260928 (Git shallow)"
SPEC_SCHEMA = "kit.freecad.baked-source-spec.v1"
LOCK_SCHEMA = "kit.freecad.baked-source-lock.v1"
OWNER = "Specimen"
DRIVERS = ("Length", "Width", "Height")
BOX = "Part::Box"
BAKED = "Part::Feature"
REFERENCE = {"label": "Health control", "origin_mm": (0.0, 0.0, -5.0), "size_mm": (37.0, 21.0, 16.0)}
POSITIONS = frozenset(product((0, 1), repeat=3))
AXIS_EDGES = frozenset(frozenset(pair) for pair in combinations(POSITIONS, 2)
                       if sum(a != b for a, b in zip(*pair, strict=True)) == 1)
FILETIME_EPOCH = 116444736000000000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def external_path(text):
    path = Path(text)
    require(path.is_absolute(), "custody paths must be absolute")
    resolved = path.resolve()
    require(not path.is_symlink() and not any((parent / ".git").exists()
                for parent in (resolved, *resolved.parents)), "custody paths must be outside checkouts")
    return resolved


def digest_file(path):
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pinned_json(path, expected):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected, "custody input SHA-256 differs")
    return json.loads(raw, object_pairs_hook=unique_keys)


def unique_keys(pairs):
    result = dict(pairs)
    require(len(result) == len(pairs), "custody JSON has duplicate fields")
    return result


def json_data(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def write_receipt(path, value):
    raw = json_data(value)
    with path.open("xb") as stream:
        stream.write(raw)
    return sha256(raw).hexdigest()


def number(value):
    require(type(value) in (int, float) and isfinite(value), "a finite numeric input is required")
    return float(value)


def case_input(value, kind):
    expected = {"label", "origin_mm", "size_mm"}
    if kind == BOX:
        expected.add("edited_length_mm")
    require(type(value) is dict and set(value) == expected, "source case fields differ from the schema")
    label = value["label"]
    require(type(label) is str and label.strip() and label.isprintable(), "a printable source label is required")
    require(all(type(value[key]) is list and len(value[key]) == 3 for key in ("origin_mm", "size_mm")),
            "source coordinates and lengths must be triples")
    origin, size = (tuple(map(number, value[key])) for key in ("origin_mm", "size_mm"))
    require(all(step > 0 and isfinite(start + step) and start + step > start
                for start, step in zip(origin, size, strict=True)), "box extent is outside the positive finite domain")
    case = {"label": label, "origin_mm": origin, "size_mm": size}
    if kind == BOX:
        edited = number(value["edited_length_mm"])
        require(edited > 0 and edited != size[0] and isfinite(origin[0] + edited) and origin[0] + edited > origin[0],
                "control edit must change to a positive finite length")
        case["edited_length_mm"] = edited
    return case


def source_cases(spec):
    require(type(spec) is dict and set(spec) == {"schema", "baked", "negative"}
            and spec["schema"] == SPEC_SCHEMA and type(spec["baked"]) is list and len(spec["baked"]) == 2,
            "the spec needs two baked cases and one parametric control")
    first, second = (case_input(case, BAKED) for case in spec["baked"])
    require(first["size_mm"] != second["size_mm"] and first["origin_mm"] != second["origin_mm"],
            "the independent baked cases need distinct extents and origins")
    return (("Baked01", BAKED, first), ("Baked02", BAKED, second),
            ("ParametricControl", BOX, case_input(spec["negative"], BOX)))


def verify_package(executable):
    bin_path = executable.parent
    require(executable.name.casefold() == "python.exe" and bin_path.name.casefold() == "bin",
            "the interpreter must be the bundled FreeCAD executable")
    app_path = bin_path / "FreeCAD.pyd"
    part_path = bin_path.parent / "lib" / "Part.pyd"
    for path, expected in ((executable, PYTHON_EXE), (app_path, APP_MODULE),
                           (bin_path / "FreeCADApp.dll", APP_LIBRARY), (part_path, PART_MODULE)):
        require(path.is_file() and path.resolve(strict=True) == path and digest_file(path) == expected,
                f"the pinned portable FreeCAD package differs at {path.name}")
    return app_path, part_path


def verify_loader(name, path):
    require(name not in sys.modules, "native module was loaded before origin verification")
    spec = find_spec(name)
    require(spec is not None and isinstance(spec.loader, ExtensionFileLoader)
            and spec.origin is not None and Path(spec.origin).resolve(strict=True) == path,
            f"the Python loader chose an alternate {name} extension")


def windows_identity(bin_path):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    process_times = kernel.GetProcessTimes
    process_times.argtypes = (wintypes.HANDLE, *(ctypes.POINTER(wintypes.FILETIME),) * 4)
    process_times.restype = wintypes.BOOL
    times = tuple(wintypes.FILETIME() for _ in range(4))
    require(process_times(kernel.GetCurrentProcess(), *(ctypes.byref(value) for value in times)),
            "cannot observe the native process birth")
    find = kernel.GetModuleHandleW
    find.argtypes = (wintypes.LPCWSTR,)
    find.restype = wintypes.HMODULE
    module = find("FreeCADApp.dll")
    require(module, "cannot observe the loaded FreeCAD application library")
    locate = kernel.GetModuleFileNameW
    locate.argtypes = (wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD)
    locate.restype = wintypes.DWORD
    buffer = ctypes.create_unicode_buffer(32768)
    length = locate(module, buffer, len(buffer))
    library = Path(buffer.value).resolve()
    require(0 < length < len(buffer) and library == bin_path / "FreeCADApp.dll",
            "the loaded application library escaped the bundled installation")
    library_sha256 = digest_file(library)
    require(library_sha256 == APP_LIBRARY, "the loaded FreeCAD application library differs from its pin")
    started = (times[0].dwHighDateTime << 32) + times[0].dwLowDateTime
    return started, library_sha256


def runtime_identity(app, part, app_path, part_path, profile):
    version = tuple(app.Version())
    require(version[:3] == ("1", "1", "4") and version[-1] == BUILD, "FreeCAD build is outside the measured pin")
    for key in ("UserAppData", "UserParameter", "SystemParameter"):
        setting = app.ConfigGet(key)
        require(setting and Path(setting).resolve().is_relative_to(profile), "FreeCAD preferences escaped the phase profile")
    actual = tuple(Path(module.__file__).resolve(strict=True) for module in (app, part))
    require(actual == (app_path, part_path) and digest_file(app_path) == APP_MODULE
            and digest_file(part_path) == PART_MODULE,
            "FreeCAD Python modules differ from the pinned Windows distribution")
    started, library = windows_identity(app_path.parent)
    return started, {"version": list(version), "python_sha256": digest_file(Path(sys.executable)),
                     "freecad_module_sha256": APP_MODULE, "part_module_sha256": PART_MODULE,
                     "application_library_sha256": library}


def coordinate(point):
    return tuple(float(getattr(point, name)) for name in ("x", "y", "z"))


def agrees(actual, predicted):
    return isfinite(actual) and isclose(actual, predicted, rel_tol=1e-10, abs_tol=1e-9)


def station(point, bounds):
    coordinates = coordinate(point)
    hits = [tuple(i for i, allowed in enumerate(pair) if agrees(value, allowed))
            for value, pair in zip(coordinates, bounds, strict=True)]
    require(all(len(pair) == 1 for pair in hits), "source vertex does not occupy a unique box station")
    return tuple(pair[0] for pair in hits)


def box_edges(shape, bounds, part):
    observed = set()
    for edge in shape.Edges:
        require(type(edge.Curve) in (part.Line, part.LineSegment), "box edge has an alternate analytic carrier")
        endpoints = frozenset(station(vertex.Point, bounds) for vertex in edge.Vertexes)
        require(endpoints not in observed, "box edge endpoint pair repeats")
        observed.add(endpoints)
    return observed


def box_incidence(shape, bounds, part):
    require({station(vertex.Point, bounds) for vertex in shape.Vertexes} == POSITIONS,
            "source solid does not have all eight box corners")
    require(box_edges(shape, bounds, part) == AXIS_EDGES, "source boundary has alternate edge incidence")
    faces = set()
    uses = Counter()
    for face in shape.Faces:
        require(type(face.Surface) is part.Plane and len(face.Wires) == 1 and face.OuterWire.isClosed(),
                "source box face needs one closed planar trim")
        corners = {station(vertex.Point, bounds) for vertex in face.Vertexes}
        sides = [(axis, end) for axis, end in product(range(3), (0, 1))
                 if corners == {position for position in POSITIONS if position[axis] == end}]
        edges = box_edges(face, bounds, part)
        require(len(sides) == 1 and sides[0] not in faces and edges == {pair for pair in AXIS_EDGES if pair <= corners},
                "source face occupies an alternate box side or boundary")
        faces.add(sides[0])
        uses.update(edges)
    require(len(faces) == 6 and uses == Counter({edge: 2 for edge in AXIS_EDGES}), "source box boundary is not watertight")


def observe(doc, kind, case, part, settled):
    (obj,) = doc.Objects
    require(obj.Name == OWNER and obj.TypeId == kind and obj.Label == case["label"], "source object identity differs")
    state = list(obj.State)
    require(not {"Error", "Invalid", "Restore"}.intersection(state) and (not settled or "Touched" not in state),
            "source object has a native state error or remains touched after rebuild")
    require(not (obj.InList or obj.OutList or obj.ExpressionEngine or {"Proxy", "ParametricSource"}.intersection(obj.PropertiesList)),
            "source object has a live causal owner")
    expected_placement = case["origin_mm"] if kind == BOX else (0.0, 0.0, 0.0)
    require(coordinate(obj.Placement.Base) == expected_placement and tuple(obj.Placement.Rotation.Q) == (0.0, 0.0, 0.0, 1.0),
            "source object carries an alternate placement")
    drivers = tuple(float(getattr(obj, name).Value) for name in DRIVERS) if kind == BOX else ()
    require(drivers == (case["size_mm"] if kind == BOX else ()) and (kind == BOX or not set(DRIVERS).intersection(obj.PropertiesList)),
            "source does not expose the expected owned driver set")
    shape = obj.Shape
    counts = tuple(len(getattr(shape, field)) for field in ("Solids", "Shells", "Faces", "Edges", "Vertexes"))
    require(not shape.isNull() and shape.ShapeType == "Solid" and shape.isValid() and counts == (1, 1, 6, 12, 8)
            and shape.Shells[0].isClosed(), "source does not contain one valid closed rectangular solid")
    box = shape.BoundBox
    bounds = tuple((start, start + size) for start, size in zip(case["origin_mm"], case["size_mm"], strict=True))
    measurements = tuple((float(getattr(box, axis + "Min")), float(getattr(box, axis + "Max"))) for axis in "XYZ")
    lengths = case["size_mm"]
    center = coordinate(shape.CenterOfMass)
    volume, area = float(shape.Volume), float(shape.Area)
    require(volume > 0 and area > 0, "native solid must have positive volume and area")
    actual = (volume, area, *center, *(value for pair in measurements for value in pair))
    prediction = (prod(lengths), 2 * sum(a * b for a, b in combinations(lengths, 2)),
                  *(start + length / 2 for start, length in zip(case["origin_mm"], lengths, strict=True)),
                  *(value for pair in bounds for value in pair))
    require(all(agrees(value, expected) for value, expected in zip(actual, prediction, strict=True)),
            "native box differs from the independent geometry prediction")
    box_incidence(shape, bounds, part)
    return {"type": kind, "label": obj.Label, "state": state, "drivers": drivers,
            "bounds_mm": measurements, "center_mm": center, "volume_mm3": volume, "area_mm2": area, "counts": counts}


def make_source(doc, kind, case, app, part):
    obj = doc.addObject(kind, OWNER)
    obj.Label = case["label"]
    if kind == BOX:
        for name, length in zip(DRIVERS, case["size_mm"], strict=True):
            setattr(obj, name, length)
        placement = obj.Placement
        placement.Base = app.Vector(*case["origin_mm"])
        obj.Placement = placement
    else:
        x, y, z = case["origin_mm"]
        width, depth, height = case["size_mm"]
        corners = [app.Vector(x + u * width, y + v * depth, z) for u, v in ((0, 0), (1, 0), (1, 1), (0, 1), (0, 0))]
        face = part.Face(part.makePolygon(corners))
        obj.Shape = face.extrude(app.Vector(0, 0, height))
    doc.recompute()
    return obj


def control(app, part, name):
    doc = app.newDocument(name)
    try:
        make_source(doc, BOX, REFERENCE, app, part)
        return observe(doc, BOX, REFERENCE, part, True)
    finally:
        app.closeDocument(doc.Name)


def stored_props(root, kind, case):
    (declaration,) = root.findall("./Objects/Object")
    (owner,) = root.findall("./ObjectData/Object")
    require(root.tag == "Document" and root.get("ProgramVersion") == PROGRAM_VERSION
            and declaration.get("name") == owner.get("name") == OWNER
            and declaration.get("type") == kind, "stored source declaration and object data disagree")
    dependencies = root.findall("./Objects/ObjectDeps")
    require(len(dependencies) <= 1 and all(node.get("Name") == OWNER and len(node) == 0 for node in dependencies),
            "stored source declares causal dependencies")
    properties = owner.findall("./Properties/Property")
    by_name = {node.get("name"): node for node in properties}
    require(len(by_name) == len(properties) and not {"Proxy", "ParametricSource"}.intersection(by_name)
            and owner.find(".//Expression") is None, "stored source contains alternate object owners")
    for prop in properties:
        prop_type = prop.get("type", "")
        require(prop_type != "App::PropertyPythonObject", "stored source contains a Python proxy")
        if prop_type.startswith(("App::PropertyLink", "App::PropertyXLink")):
            require(len(prop) == 1 and prop[0].tag in {"Link", "LinkList", "LinkSub", "LinkSubList", "XLink", "XLinkSub", "XLinkSubList"}
                    and len(prop[0]) == 0 and not (prop[0].text or "").strip() and all(
                (name in {"count", "Count"} and text == "0") or (name in {"value", "name", "file"} and text == "")
                for name, text in prop[0].attrib.items()), "stored source has a populated or unqualified link")
    require(by_name["Label"].find("String").get("value") == case["label"], "stored source label differs")
    (shape,) = (prop for prop in properties if prop.get("type") == "Part::PropertyPartShape")
    require(shape is by_name["Shape"], "stored geometry is not the sole Shape property")
    values = tuple(by_name.get(name) for name in DRIVERS)
    if kind == BOX:
        require(all(prop is not None and prop.get("type") == "App::PropertyLength"
                    and float(prop.find("Float").get("value")) == expected
                    for prop, expected in zip(values, case["size_mm"], strict=True)), "stored control lacks its three actual drivers")
    else:
        require(all(prop is None for prop in values), "stored baked body has dimensional drivers")
    (part,) = shape.findall("./Part")
    return part.attrib["file"]


def inspect_closed_file(path, kind, case):
    require(path.is_file() and not path.is_symlink(), "the native source must be a closed ordinary file")
    raw = path.read_bytes()
    with ZipFile(BytesIO(raw)) as archive:
        members = archive.namelist()
        require(len(set(members)) == len(members) and archive.testzip() is None,
                "saved archive has duplicate or invalid members")
        xml = archive.read("Document.xml")
        member = stored_props(fromstring(xml), kind, case)
        require({name for name in members if name.casefold().endswith((".brp", ".brep"))} == {member},
                "saved archive does not contain exactly the owned Shape payload")
        shape = archive.read(member)
        require(shape, "saved Shape payload is empty")
    return {"file_sha256": sha256(raw).hexdigest(), "document_xml_sha256": sha256(xml).hexdigest(),
            "shape_sha256": sha256(shape).hexdigest(), "shape_member": member, "size": len(raw)}


def capture_source(app, part, path, name, kind, case):
    require(not path.exists(), "source output already exists")
    doc = app.newDocument(name)
    try:
        make_source(doc, kind, case, app, part)
        geometry = observe(doc, kind, case, part, True)
        doc.saveAs(str(path))
    finally:
        app.closeDocument(doc.Name)
    return {"geometry": geometry, "archive": inspect_closed_file(path, kind, case)}


def edit_control(doc, part, case):
    (obj,) = doc.Objects
    edited = dict(case, size_mm=(case["edited_length_mm"], *case["size_mm"][1:]))
    obj.Length = edited["size_mm"][0]
    doc.recompute()
    changed = observe(doc, BOX, edited, part, True)
    obj.Length = case["size_mm"][0]
    doc.recompute()
    restored = observe(doc, BOX, case, part, True)
    return {"changed": changed, "restored": restored}


def reopen_source(app, part, path, kind, case, expected_archive):
    require(inspect_closed_file(path, kind, case) == expected_archive, "closed source differs from its author pin")
    doc = app.openDocument(str(path))
    require(doc is not None, "native reopen failed to return the source")
    try:
        require(Path(doc.FileName).resolve() == path, "native reopen selected an alternate source")
        cold = observe(doc, kind, case, part, False)
        (obj,) = doc.Objects
        obj.touch()
        doc.recompute()
        rebuilt = observe(doc, kind, case, part, True)
        edit = edit_control(doc, part, case) if kind == BOX else None
    finally:
        app.closeDocument(doc.Name)
    require(digest_file(path) == expected_archive["file_sha256"], "native reopen changed the original archive")
    return {"cold": cold, "rebuilt": rebuilt, "live_edit": edit}


def publish_lock(packet, author_sha, reopen_sha, current, author, cases):
    inputs = []
    for name, kind, _ in cases:
        archived = author["cases"][name]["archive"]
        inputs.append({key: archived[key] for key in ("file_sha256", "document_xml_sha256", "shape_sha256")}
                      | {"standalone_baked": kind == BAKED, "object_count": 1, "solid_count": 1})
    require(len({entry["file_sha256"] for entry in inputs}) == len(cases)
            and len({entry["shape_sha256"] for entry in inputs if entry["standalone_baked"]}) == 2,
            "independent sources have duplicate identities")
    require(current["cases"]["ParametricControl"]["live_edit"] is not None, "negative control lacks proof of editable geometry")
    lock = {"schema": LOCK_SCHEMA, "passed": True, "baked_sources": 2, "parametric_controls": 1,
            "native_processes": 2, "healthy_brackets": 4, "live_parametric_controls": 1,
            "tool_sha256": current["tool_sha256"], "spec_sha256": current["spec_sha256"], "build_sha": BUILD,
            "runtime_sha256": sha256(json_data(current["runtime"])).hexdigest(), "author_sha256": author_sha,
            "reopen_sha256": reopen_sha, "inputs": inputs, "writer_outputs": 0, "fcstd_conversion_credit": 0}
    return write_receipt(packet / "PrewriterSourceLock01.json", lock)


def run_phase(args, packet, cases, profile, app_path, part_path):
    bin_path = app_path.parent
    lib_path = part_path.parent
    with os.add_dll_directory(str(bin_path)), os.add_dll_directory(str(lib_path)):
        sys.path[:0] = (str(bin_path), str(lib_path))
        verify_loader("FreeCAD", app_path)
        verify_loader("Part", part_path)
        import FreeCAD as app
        import Part as part

        started, runtime = runtime_identity(app, part, app_path, part_path, profile)
        report = {"runtime": runtime, "tool_sha256": args.tool_sha256, "spec_sha256": args.spec_sha256,
                  "phase": args.phase, "process_birth": started, "pid": os.getpid(), "passed": True}
        require(not app.listDocuments(), "native instance already owns documents")
        if args.phase == "reopen":
            previous = pinned_json(packet / "NativeAuthor.json", args.author_sha256)
            require(previous["phase"] == "author" and previous["passed"] is True
                    and previous["runtime"] == runtime and previous["tool_sha256"] == args.tool_sha256
                    and previous["spec_sha256"] == args.spec_sha256 and previous["pid"] != os.getpid()
                    and previous["ended_filetime"] < started
                    and set(previous["cases"]) == {name for name, _, _ in cases}, "native author receipt or process chronology differs")
        report["before"] = control(app, part, "Before")
        observed = {}
        for name, kind, case in cases:
            source = packet / (name + ".FCStd")
            if args.phase == "author":
                observed[name] = capture_source(app, part, source, name, kind, case)
            else:
                observed[name] = reopen_source(app, part, source, kind, case, previous["cases"][name]["archive"])
        report["cases"] = observed
        report["after"] = control(app, part, "After")
        require(not app.listDocuments(), "native instance did not close all documents")
        report["ended_filetime"] = time_ns() // 100 + FILETIME_EPOCH
    if args.phase == "author":
        return {"passed": True, "authors_completed": 3,
                "author_sha256": write_receipt(packet / "NativeAuthor.json", report), "locked": False}
    reopen_sha = write_receipt(packet / "NativeReopen.json", report)
    lock_sha = publish_lock(packet, args.author_sha256, reopen_sha, report, previous, cases)
    return {"passed": True, "sources_locked": 3, "lock_sha256": lock_sha, "locked": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("author", "reopen"))
    parser.add_argument("packet")
    parser.add_argument("spec")
    parser.add_argument("--runtime-python", required=True)
    parser.add_argument("--tool-sha256", required=True)
    parser.add_argument("--spec-sha256", required=True)
    parser.add_argument("--author-sha256")
    args = parser.parse_args()
    require(sys.platform == "win32" and sys.version_info >= (3, 10), "use the pinned FreeCAD Windows bundled Python")
    require(digest_file(Path(__file__).resolve()) == args.tool_sha256, "collector SHA-256 differs from the frozen method")
    require((args.author_sha256 is not None) == (args.phase == "reopen"), "only reopen requires the author receipt SHA-256")
    packet, spec = (external_path(value) for value in (args.packet, args.spec))
    require(not spec.is_relative_to(packet), "the frozen spec must be outside the packet")
    cases = source_cases(pinned_json(spec, args.spec_sha256))
    executable = external_path(args.runtime_python)
    require(executable == Path(sys.executable).resolve(strict=True), "the executable must match the bundled runtime argument")
    app_path, part_path = verify_package(executable)
    if args.phase == "author":
        packet.mkdir()
    else:
        require(packet.is_dir() and not any((packet / name).exists() for name in ("NativeReopen.json", "PrewriterSourceLock01.json")),
                "reopen needs the original unfinished packet")
        pinned_json(packet / "NativeAuthor.json", args.author_sha256)
    profile = packet / (args.phase + "-profile")
    profile.mkdir()
    configure_profile(profile)
    print(json.dumps(run_phase(args, packet, cases, profile, app_path, part_path), sort_keys=True))


def configure_profile(profile):
    for variable, child in {"APPDATA": "Roaming", "LOCALAPPDATA": "Local", "TEMP": "Temp", "TMP": "Temp",
                            "XDG_CONFIG_HOME": "Config", "XDG_CACHE_HOME": "Cache", "XDG_DATA_HOME": "Data",
                            "FREECAD_USER_HOME": "FreeCAD"}.items():
        directory = profile / child
        directory.mkdir(exist_ok=True)
        os.environ[variable] = str(directory)
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


if __name__ == "__main__":
    main()
