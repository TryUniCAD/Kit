from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch


HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
EVENT = 1794974400
FORMAT = "solidworks.sldprt"
FREEZE_SHA = "0d9655b482e7aa46f80ddc2a000fd597f6a869a55c481aa227e9b9b9c9b0e987"
NATIVE_SHA = "e94dd631acd5942a53296f36b77d1c3bc8b321e8ba7fd725327c74ac4a12916c"
SOURCE_SHA = "c1499c173a495b0186e3acf733fcfb02b7bdb94fc46a6a902768fedec44d0e72"
READ_SHA = "d0f92416cf7aaec2abc773b3923e685fb117bbb594563b8fdba7375b04fc4ef3"
READER = "re/tooling/sw2026/CheckSdkCircleRead.py"
GUARD = "src/convert/adapters/solidworks/Core/Preparation/Circle/CheckCircMode.py"
EXPECTED_CAPS = frozenset(("parameters", "parametric_history", "support_planes",
                           "editable_sketches", "body_structure", "configurations"))
PROFILES = {
    "H03MidPlane": ["x", "Right Plane", True, False, "mid_plane", False],
    "H04TwoDirections": ["y", "Top Plane", True, True, "two_directions", True],
    "sdk public front diameter": ["z", "Front Plane", True, False, "blind", False],
    "sdk public top radius": ["y", "Top Plane", False, True, "blind", False],
}
REACHED_GUARD = "circle preparation is not qualified for this support driver or end profile"
POLICY = {"require_native_transfers": True}
PROCESS_EVENTS = ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.fork", "os.forkpty", "ctypes.dlopen")
DIRECTORY_EVENTS = ("os.listdir", "os.scandir")
ACCESS_MODE_MASK = getattr(os, "O_ACCMODE", os.O_WRONLY | os.O_RDWR)
EDIT_EVENTS = ("os.mkdir", "os.rmdir", "os.remove", "os.unlink", "os.rename", "os.link", "tempfile.mkdtemp")


def require(flag, text):
    if not flag:
        raise ValueError(text)


def identity(value):
    return {"bytes": len(value), "sha256": sha256(value).hexdigest()}


def locked(path, expected):
    data = path.read_bytes()
    require(identity(data)["sha256"] == expected, "custody hash differs: " + path.name)
    return data


def read_json(path, checksum):
    return json.loads(locked(path, checksum))


class OutputGuard:
    def __init__(self, root, filename):
        self.root = root.resolve()
        self.filename = filename
        self.mode = None
        self.directories = {}
        self.events = Counter()
        self.denied = []

    @contextmanager
    def active(self, mode):
        self.mode = mode
        try:
            yield
        finally:
            self.mode = None
        require(not self.denied, "the writer attempted a prohibited runtime operation")

    def event_path(self, path, fd=-1):
        if type(path) is int:
            state = os.fstat(path)
            return self.directories.get((state.st_dev, state.st_ino))
        if not isinstance(path, (str, bytes)):
            return None
        value = Path(os.fsdecode(path))
        if not value.is_absolute():
            parent = self.event_path(fd) if type(fd) is int and fd >= 0 else None
            if parent is None:
                return None
            value = parent / value
        value = value.resolve()
        return value if value.is_relative_to(self.root) else None

    def denied_event(self, name, args):
        self.denied.append(name)
        raise PermissionError(f"unattributed writer operation: {name}: {args!r}")

    def audit(self, name, args):
        if self.mode is None or name not in (*PROCESS_EVENTS, *DIRECTORY_EVENTS, *EDIT_EVENTS, "open"):
            return
        if name in PROCESS_EVENTS or self.mode != "path":
            self.denied_event(name, args)
        if name == "open":
            path = self.event_path(args[0])
            if path is None:
                self.denied_event(name, args)
            if path.is_dir():
                state = path.stat()
                self.directories[(state.st_dev, state.st_ino)] = path
            elif path.name != self.filename or args[2] & ACCESS_MODE_MASK != os.O_WRONLY:
                self.denied_event(name, args)
        elif name in ("os.rename", "os.link"):
            source, target, source_fd, target_fd = args
            if self.event_path(source, source_fd) is None or self.event_path(target, target_fd) is None:
                self.denied_event(name, args)
        else:
            fd = args[2] if name == "os.mkdir" else args[1] if name in ("os.rmdir", "os.remove", "os.unlink") else -1
            if self.event_path(args[0], fd) is None:
                self.denied_event(name, args)
        self.events[name] += 1


def profile(plan):
    end = plan.EndValue
    return [plan.AxisValue, plan.PlaneName, plan.IsDiameter, end.IsReversed,
            end.ModeValue, end.SecondDepth is not None]


def check_transfer(result, payload, expected_path):
    from convert.adapters.base.TransferContract import TransferMode

    transfers = {item.capability.value: item.mode for item in result.transfers}
    require(result.path == expected_path and result.adapter == FORMAT and result.bytes_written == len(payload) and
            result.vendor_loadable and result.application_usable and
            not result.dropped and not result.carrier_capabilities and not result.requirements and
            len(result.transfers) == len(EXPECTED_CAPS) and set(transfers) == EXPECTED_CAPS and
            all(mode is TransferMode.KNative for mode in transfers.values()) and
            {item.value for item in result.native_capabilities} == EXPECTED_CAPS,
            "a public capability transfer or publication result differs")
    return {name: mode.value for name, mode in sorted(transfers.items())}


def read_generated(sdk, helper, target, document, plan, archive_sha):
    from importlib.util import module_from_spec, spec_from_file_location

    locked(helper, READ_SHA)
    spec = spec_from_file_location("public_circle_output_reader", helper)
    probe = module_from_spec(spec)
    spec.loader.exec_module(probe)
    (geometry,) = (entity.geometry for entity in document.sketches[0].entities)
    end = document.feature_timeline[0].definition
    request = {"path": str(target), "sha256": archive_sha, "case": plan.NameValue, "phase": "public-generated",
               "axis": plan.AxisValue, "feature": plan.FeatureName, "mode": "diameter" if plan.IsDiameter else "radius",
               "center_mm": [geometry.center.x, geometry.center.y], "radius_mm": geometry.radius,
               "depth_mm": end.length.value, "second_mm": None if end.second_length is None else end.second_length.value,
               "reverse": end.reversed, "end_condition": plan.EndValue.ModeValue}
    previous = sys.stdin
    try:
        sys.stdin = StringIO(json.dumps(request, allow_nan=False))
        answer = probe.worker(sdk)
    finally:
        sys.stdin = previous
    require(answer["passed"] and answer["typed_streams_exact"] == 2, "generated Config/Resolved did not read back exactly")
    answer.pop("pid")
    return answer


def admitted(data, sdk, folder, document):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.api.ApiContext import GetRegistry

    name = document.metadata["name"]
    target = folder / "output" / (name + ".SLDPRT")
    audit = OutputGuard(folder, target.name)
    sys.addaudithook(audit.audit)
    writer = GetRegistry().GetWriter(FORMAT)
    options = {**POLICY, "final_destination": str(target)}
    event = data["request"]["created_at"]
    require(event == EVENT, "use the original measured event")
    with patch("convert.adapters.solidworks.Core.Writing.EmitNativeMut.ReadTime", return_value=event) as clock:
        with audit.active("memory"):
            plan = PlanNativePart(document)
            require(profile(plan) == PROFILES[name] and writer.supports(document, target), "registry does not admit the measured profile")
            stream = BytesIO()
            settings = WriteOptions(values=options)
            recipe = MakePartRecipe(plan, event)
            locator = FinalPartPath(stream, settings, recipe.OutputValue, name).PathName
            prepared = PrepareNative(document, BytesIO(), event, settings)
            stream_result = write_document(document, stream, destination_format=FORMAT, allow_carrier=False, values=options)
        with audit.active("path"):
            path_result = write_document(document, target, allow_carrier=False, values=POLICY)
    require(clock.call_count == 2 and not audit.denied and audit.events["open"] >= 1, "the real path and stream emission were not both observed")
    payload = target.read_bytes()
    require(prepared.BytesValue == stream.getvalue() == payload and
            locator == "C:\\KitSdkCandidates\\" + target.name, "the preparation paths changed bytes or the synthetic locator")
    archive = SldprtArchive.from_bytes(payload)
    streams = {row.name: identity(row.data) for row in archive.records}
    require(archive.format_version == 4 and len(streams) == 10 and
            streams == {name: identity(value) for name, value in prepared.StreamsValue.items()},
            "the published bytes do not carry the complete prepared part")
    if data["measured"] is not None:
        source = data["measured"]
        require(identity(payload) == source["artifact"] and streams == source["streams"] and
                locator == source["stored_self_path"], "the exact native prediction or standard stream bytes changed")
    transfers = check_transfer(path_result, payload, target)
    require(check_transfer(stream_result, payload, None) == transfers, "path and stream transfers differ")
    readback = read_generated(sdk, Path(data["reader"]), target, document, plan, identity(payload)["sha256"])
    return {"name": name, "profile": profile(plan), "event": event, "stored_self_path": locator,
            "artifact": identity(payload), "streams": streams, "native_transfers": transfers,
            "path_staging_events": dict(audit.events), "runtime_input_reads": 0, "cad_launches": 0,
            "readback": readback}


def flip_direction(document):
    feature, = document.feature_timeline
    return replace(document, feature_timeline=(replace(feature, definition=replace(feature.definition, reversed=not feature.definition.reversed)),))


def switch_driver(document):
    sketch, = document.sketches
    circle, = sketch.entities
    relations = tuple(replace(row, kind="radius" if row.kind == "diameter" else "diameter")
                      if row.kind in ("radius", "diameter") else row for row in sketch.constraints)
    radial = next(row for row in relations if row.parameter_id)
    parameters = tuple(replace(row, value=replace(row.value, value=circle.geometry.radius * (2 if radial.kind == "diameter" else 1)))
                       if row.id == radial.parameter_id else row for row in document.parameters)
    return replace(document, parameters=parameters, sketches=(replace(sketch, constraints=relations),))


def negative_models(first, second, front, top):
    from interchange.Enums.EnumUnits import UnitSystem
    from interchange.Features.FeatureExtrude import ExtrudeEnd
    from interchange.geometry.Models.VectorPlane import PlaneVector

    plane, = first.support_planes
    forward, = front.support_planes
    feature, = second.feature_timeline
    wider = replace(feature.definition, second_end_condition=ExtrudeEnd.KMidPlane)
    sketch, = first.sketches
    circle, = sketch.entities
    geometry = replace(circle.geometry, radius=circle.geometry.radius / 1000,
                       center=PlaneVector(circle.geometry.center.x / 1000, circle.geometry.center.y / 1000))
    metres = replace(first, units=UnitSystem.KMeter, sketches=(replace(sketch, entities=(replace(circle, geometry=geometry),)),))
    return (
        ("midplane-reversed", flip_direction(first), True),
        ("midplane-radius", switch_driver(first), True),
        ("midplane-foreign-name", replace(first, support_planes=(replace(plane, name="Unused plane"),)), True),
        ("midplane-front", replace(first, support_planes=(replace(plane, name=forward.name, transform=forward.transform),)), True),
        ("midplane-metres", metres, True),
        ("two-direction-forward", flip_direction(second), True),
        ("two-direction-radius", switch_driver(second), True),
        ("two-direction-wrong-second-mode", replace(second, feature_timeline=(replace(feature, definition=wider),)), False),
        ("blind-front-radius", switch_driver(front), True),
        ("blind-top-diameter", switch_driver(top), True),
    )


def refuses(launch, errors):
    try:
        launch()
    except errors as exc:
        return str(exc)
    raise ValueError("an unsupported profile reached publication")


def rejected(folder, documents):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.registry.RegistryErrors import RegistryError
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
    from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.api.ApiContext import GetRegistry

    writer = GetRegistry().GetWriter(FORMAT)
    results = []
    for name, document, coherent in negative_models(*documents):
        filename = document.metadata["name"] + ".SLDPRT"
        fresh = folder / name / filename
        prior = folder / (name + "-prior") / filename
        prior.parent.mkdir()
        sentinel = ("untouched publication control " + name).encode()
        prior.write_bytes(sentinel)
        guard = OutputGuard(folder, filename)
        sys.addaudithook(guard.audit)
        stream = BytesIO()
        opts = {**POLICY, "final_destination": str(fresh)}
        with guard.active("memory"):
            if coherent:
                ProjectCircle(document)
            plan_error = refuses(lambda: PlanNativePart(document), (ValueError, TypeError))
            if coherent:
                require(plan_error == REACHED_GUARD, "a coherent near miss did not reach the exact mode guard")
            require(not writer.supports(document, fresh) and not writer.supports(document, stream),
                    "the registered selector admits an unsupported profile")
            preparation_error = refuses(lambda: PrepareNative(document, stream, EVENT, WriteOptions(values=opts)), (ValueError, TypeError))
            require(plan_error == preparation_error, "selection and preparation refusals differ")
            refuses(lambda: write_document(document, fresh, allow_carrier=False, values=POLICY), (RegistryError,))
            refuses(lambda: write_document(document, prior, overwrite=True, allow_carrier=False, values=POLICY), (RegistryError,))
            refuses(lambda: write_document(document, stream, destination_format=FORMAT, allow_carrier=False, values=opts), (RegistryError,))
        require(not guard.events and not guard.denied and not fresh.parent.exists() and prior.read_bytes() == sentinel and not stream.getvalue(),
                "a refused profile altered a destination or reached staging")
        results.append({"name": name, "coherent": coherent, "diagnostic": plan_error,
                        "new_path_absent": True, "existing_path_unchanged": True, "stream_empty": True})
    admitted_case = documents[0]
    wrong = folder / "wrong-name.SLDPRT"
    config = folder / "wrong-config" / (admitted_case.metadata["name"] + ".SLDPRT")
    guard = OutputGuard(folder, config.name)
    sys.addaudithook(guard.audit)
    with guard.active("memory"):
        require(not writer.supports(admitted_case, wrong), "a foreign basename reached admission")
        refuses(lambda: write_document(admitted_case, wrong, allow_carrier=False, values=POLICY), (RegistryError,))
    with guard.active("path"):
        refuses(lambda: write_document(admitted_case, config, configuration="Unknown", allow_carrier=False, values=POLICY),
                (RegistryError, ValueError))
    require(not wrong.exists() and not config.parent.exists(), "a refused destination policy was published")
    return {"profiles": results, "destination_refusals": ["foreign-basename", "unknown-configuration"]}


def worker():
    data = json.load(sys.stdin)
    sdk = Path(data["sdk"])
    sys.path[:0] = [str(sdk / "src"), str(sdk)]
    from interchange.serialization.Deserialize import FromData

    for codec in ("utf-16-le", "utf-8", "latin-1"):
        lookup(codec)
    for module in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        import_module("interchange.document.Validation." + module)
    for module in ("DocumentProvenance", "DocumentWalk"):
        import_module("interchange.document.Models." + module)
    with TemporaryDirectory(prefix="part-write-", dir=data["scratch"]) as scratch:
        folder = Path(scratch).resolve()
        if data["mode"] == "admitted":
            return admitted(data, sdk, folder, FromData(data["request"]["document"]))
        require(data["mode"] == "rejected", "unknown public proof worker role")
        return rejected(folder, tuple(FromData(request["document"]) for request in data["requests"]))


def isolated(data):
    result = subprocess.run([sys.executable, "-I", "-B", str(HERE), "worker"],
                            input=json.dumps(data, allow_nan=False).encode(), capture_output=True,
                            check=False, timeout=120)
    label = data.get("request", {}).get("document", {}).get("metadata", {}).get("name", data["mode"])
    require(result.returncode == 0, str(label) + ": " + result.stderr.decode(errors="replace"))
    return json.loads(result.stdout)


def authored_blind_controls():
    sys.path[:0] = [str(REPO / "src"), str(REPO)]
    from interchange.serialization.EncodeData import ToData
    from tests.Convert.Solidworks.Research.AdapterBridge.Circles.MakeWriteCircle import MakeWriteCircle

    return [{"document": ToData(MakeWriteCircle(name, is_top)), "created_at": EVENT}
            for name, is_top in (("sdk public front diameter", False), ("sdk public top radius", True))]


def frozen_cases(workspace):
    frozen = read_json(workspace / "GeneratedFreeze.json", FREEZE_SHA)
    native = read_json(workspace / "Packet/Inspection/Result.json", NATIVE_SHA)
    require(frozen["passed"] and native["passed"] and native["inputs_immutable"] and
            native["controls_healthy"] and native["native_processes"] == native["distinct_processes"] == 14,
            "the exact generated or native lifecycle does not qualify")
    rows = []
    for case, observed in zip(frozen["cases"], native["cases"], strict=True):
        name = case["name"]
        directory = workspace / "Generated" / name
        request = read_json(directory / "Request.json", case["request_sha256"])
        built = read_json(directory / "Build.json", case["build_sha256"])
        require(name == observed["name"] and built["sha256"] == case["candidate_sha256"] ==
                observed["lanes"]["generated"][0]["source_sha256"] and
                built["bytes"] == case["candidate_bytes"] and request["created_at"] == EVENT,
                "the neutral case does not bind the measured native candidate")
        require("blob" not in built, "the public proof consumes hashes and neutral requests only")
        rows.append((request, {"artifact": {"bytes": built["bytes"], "sha256": built["sha256"]},
                               "streams": built["streams"], "stored_self_path": built["stored_self_path"],
                               "request_sha256": case["request_sha256"]}))
    require([row[0]["document"]["metadata"]["name"] for row in rows] == ["H03MidPlane", "H04TwoDirections"],
            "the public proof requires both original qualified profiles")
    return rows


def verify_baseline(workspace):
    frozen = read_json(workspace / "SDK/FrozenSource.json", SOURCE_SHA)
    repo = workspace / "SDK/Kit"
    require(frozen["file_count"] == len(frozen["files_sha256"]) == 5017 and frozen["files_sha256"][READER] == READ_SHA and GUARD in frozen["files_sha256"],
            "the qualified existing writer and reader freeze differs")
    for path, checksum in frozen["files_sha256"].items():
        source = repo / path
        require(not source.is_symlink() and source.resolve(strict=True).is_relative_to(repo), "source escapes the baseline SDK")
        locked(source, checksum)
    return repo, frozen["base"], frozen["files_sha256"][GUARD]


def live_sources():
    entries = subprocess.check_output(("git", "-C", str(REPO), "ls-files", "-z", "--", "src"))
    names = sorted(name.decode() for name in entries.split(b"\0") if name)
    result = sha256()
    for name in names:
        source = REPO / name
        require(not source.is_symlink() and source.resolve(strict=True).is_relative_to(REPO), "source escapes the production checkout")
        result.update(name.encode() + b"\0" + identity(source.read_bytes())["sha256"].encode() + b"\n")
    return {"files": len(names), "sha256": result.hexdigest()}


def main():
    parser = ArgumentParser(description="Prove exact registered circle-end emission from the two locked neutral requests")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    workspace = arguments.workspace.resolve(strict=True)
    output = arguments.output.resolve()
    require(not output.exists() and not output.is_relative_to(workspace) and not output.is_relative_to(REPO),
            "use a fresh output directory outside the packet and repository")
    baseline, base_revision, prior_guard = verify_baseline(workspace)
    cases = frozen_cases(workspace)
    controls = authored_blind_controls()
    output.mkdir(parents=True)
    reader = baseline / READER
    tool_identity = identity(HERE.read_bytes())["sha256"]
    writer_identity = identity((REPO / GUARD).read_bytes())["sha256"]
    code_revision = subprocess.check_output(("git", "-C", str(REPO), "rev-parse", "HEAD"), text=True).strip()
    source_inventory = live_sources()
    comparison = {"scratch": str(output), "reader": str(reader)}
    positive = []
    for request, measured in cases:
        record = isolated({**comparison, "sdk": str(REPO), "mode": "admitted", "request": request, "measured": measured})
        positive.append({**record, "request_sha256": measured["request_sha256"]})
    blind = []
    for request in controls:
        control = {**comparison, "mode": "admitted", "request": request, "measured": None}
        before = isolated({**control, "sdk": str(baseline)})
        after = isolated({**control, "sdk": str(REPO)})
        require(before == after, "an already qualified blind control changed")
        blind.append(after)
    refusals = isolated({**comparison, "sdk": str(REPO), "mode": "rejected", "requests": [*(row[0] for row in cases), *controls]})
    require(verify_baseline(workspace) == (baseline, base_revision, prior_guard) and frozen_cases(workspace) == cases and
            identity(HERE.read_bytes())["sha256"] == tool_identity and live_sources() == source_inventory and
            identity((REPO / GUARD).read_bytes())["sha256"] == writer_identity,
            "proof or input custody changed during registration")
    report = {"schema": "kit.sw2026.sdk-circle-end-registration.v1", "passed": True, "sdk_worktree_base": code_revision,
              "sdk_source_inventory": source_inventory,
              "production_guard_sha256": writer_identity, "tool_sha256": tool_identity,
              "native_sha256": NATIVE_SHA, "generated_freeze_sha256": FREEZE_SHA,
              "baseline_sdk_source_sha256": SOURCE_SHA, "baseline_sdk_source_revision": base_revision,
              "baseline_guard_sha256": prior_guard, "exact_original_event": EVENT,
              "native_identical_public_profiles": positive, "byte_identical_existing_blinds": blind,
              "fresh_sdk_processes": 7, "public_path_and_stream_writes": 12, "refusals": refusals,
              "standard_properties_match_complete_streams": True, "runtime_vendor_reads": 0, "cad_launches": 0}
    payload = (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with (output / "Registration.json").open("xb") as sink:
        sink.write(payload)
    print(json.dumps({"passed": True, "sha256": identity(payload)["sha256"], "native_identical_profiles": len(positive),
                      "blind_controls": len(blind), "model_refusals": len(refusals["profiles"]),
                      "destination_refusals": len(refusals["destination_refusals"])}, sort_keys=True))


if __name__ == "__main__":
    if sys.argv[1:] == ["worker"]:
        print(json.dumps(worker(), sort_keys=True, allow_nan=False))
    else:
        main()
