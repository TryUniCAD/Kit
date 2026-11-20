from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
from subprocess import check_output, run
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
RESEARCH = HERE.parents[2]
FROZEN = "6fc230fb31c3195ff16da5327d4a872f51e49290"
FORMAT = "solidworks.sldprt"
LEGACY = ("blind", "circle", "equation", "import")
PATCHED = tuple(
    "src/convert/adapters/solidworks/Core/" + name
    for name in (
        "Preparation/IsStockChain.py",
        "Preparation/PlanNativePart.py",
        "Preparation/PrepareNative.py",
        "Writing/EmitNativeMut.py",
        "Writing/SldWriteInfo.py",
    )
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_runtime(sdk):
    sys.path[:0] = [
        str(sdk), str(ROOT), str(HERE.parent), str(HERE.parent.parent / "twostockshape"),
        str(RESEARCH), str(RESEARCH / "equations"),
    ]
    for module in (
        "convert",
        "convert.adapters.solidworks.Core.Writing.EmitNativeMut",
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.serialization.Deserialize",
    ):
        owner = import_module(module)
        require(Path(owner.__file__).is_relative_to(sdk), "an unpinned SDK import was reached: " + module)
    from ProveSdkStockWriter import STAMP

    emitter = sys.modules["convert.adapters.solidworks.Core.Writing.EmitNativeMut"]
    emitter.ReadTime = lambda: STAMP
    for encoding in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        lookup(encoding)


def policy_result(result, data, qualified, where, expected=None):
    require(
        result.path == where
        and result.adapter == FORMAT
        and result.bytes_written == len(data)
        and result.application_usable is qualified
        and result.vendor_loadable is qualified
        and not result.carrier_capabilities
        and not result.dropped
        and not result.requirements,
        "publication result violated SDK write policy",
    )
    native = sorted(cap.value for cap in result.native_capabilities)
    if expected is not None:
        require(native == sorted(expected), "a real native transfer was omitted or misclassified")
    return native


def stock_worker(folder):
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import PrepareStockPart
    from convert.adapters.solidworks.Core.Preparation.TwoStock.TwoStockPlan import TwoStockPlan
    from convert.adapters.solidworks.Core.Writing.EmitNativeMut import EmitNativeMut
    from convert.api.ApiContext import GetRegistry
    from ProveSdkStockWriter import authored, HISTORICAL_HASH, fingerprint, PART, STAMP
    from VerifySdkCircleEndRegistration import OutputGuard

    document = authored("disclosed")
    filename = PART + ".SLDPRT"
    destination = rf"C:\KitSdkCandidates\{filename}"
    direct_path = folder / filename
    audit = OutputGuard(folder, filename)
    sys.addaudithook(audit.audit)
    adapter = GetRegistry().GetWriter(FORMAT)
    stream_policy = {
        "final_destination": destination, "require_native_transfers": True,
    }
    options = WriteOptions(values=stream_policy)
    with audit.active("memory"):
        require(
            isinstance(PlanNativePart(document), TwoStockPlan)
            and adapter.supports(document, BytesIO())
            and adapter.supports(document, direct_path)
            and GetDocumentCaps(document) <= adapter.info.NativeCaps,
            "the candidate planning and capability checks disagree",
        )
        prepared = PrepareStockPart(document, BytesIO(), STAMP, options)
        dispatched = PrepareNative(document, BytesIO(), STAMP, options)
        direct = BytesIO()
        bound = EmitNativeMut(document, direct, options)
    with audit.active("path"):
        file_result = EmitNativeMut(document, direct_path, None)
    payload = direct_path.read_bytes()
    streams = SldprtArchive.from_bytes(payload).streams
    identity = fingerprint(streams, payload)
    require(
        payload == direct.getvalue() == prepared.BytesValue == dispatched.BytesValue
        and streams == prepared.StreamsValue == dispatched.StreamsValue
        and identity["sha256"] == HISTORICAL_HASH and len(streams) == 10
        and tuple(folder.iterdir()) == (direct_path,),
        "the internal dispatch changed the frozen archive or opened an extra file",
    )
    for result, path in ((bound, None), (file_result, direct_path)):
        policy_result(result, payload, False, path)
    return {
        "artifact": identity, "internal_equal_routes": 4,
        "inferred_capabilities": sorted(cap.value for cap in GetDocumentCaps(document)),
        "application_usable": False, "vendor_loadable": False,
        "guarded_path_events": dict(audit.events), "runtime_input_file_reads": 0,
    }


def refusals_worker(folder):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.api.ApiContext import GetRegistry
    from interchange.geometry.Models.Selection import SelectPathElem, Selection
    from ProveSdkStockWriter import authored, damage, PART, STAMP
    from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc
    from VerifySdkCircleEndRegistration import OutputGuard, refuses

    document = authored("disclosed")
    filename = PART + ".SLDPRT"
    destination = folder / "existing" / filename
    destination.parent.mkdir()
    sentinel = b"independent prior destination"
    destination.write_bytes(sentinel)
    stream = BytesIO(sentinel)
    options = {"final_destination": rf"C:\KitSdkCandidates\{filename}",
               "require_native_transfers": True}
    guard = OutputGuard(folder, filename)
    sys.addaudithook(guard.audit)
    adapter = GetRegistry().GetWriter(FORMAT)
    unknown = folder / "never-created" / filename
    fresh = folder / "strictly-refused" / filename
    legacy = MakePlainDoc("LegacySelectionRefused", 37.9, 18.2, 9.1)
    choice = Selection("p", "Extra unmodeled pick",
                       (SelectPathElem("feature", legacy.feature_timeline[0].id, "body"),))
    legacy = replace(legacy, selections=(choice,))
    with guard.active("memory"):
        bad = damage(document, "foreign-body-pick")
        require(
            not adapter.supports(bad, unknown)
            and not adapter.supports(legacy, BytesIO())
            and not adapter.supports(document, unknown.with_suffix(".SLDASM"))
            and not adapter.supports(document, unknown.with_name("OtherName.SLDPRT")),
            "selection capability opened an unrelated profile or target",
        )
        denied = refuses(
            lambda: write_document(
                document, stream, destination_format=FORMAT, allow_carrier=False, values=options,
            ),
            (ValueError,),
        )
        refuses(lambda: write_document(bad, unknown, allow_carrier=True), (NotFoundError,))
        missing = refuses(
            lambda: PrepareNative(document, stream, STAMP, WriteOptions()),
            (ValueError,),
        )
        require("explicit final destination" in missing,
                "a nameless prepared stream did not reach the locator guard")
        refused = refuses(
            lambda: write_document(
                document, destination, overwrite=True, allow_carrier=True,
                values={"require_native_transfers": True},
            ),
            (ValueError,),
        )
        readonly = refuses(lambda: write_document(document, fresh, allow_carrier=True), (ValueError,))
        direct = refuses(lambda: adapter.write(document, destination, WriteOptions(overwrite=True)), (ValueError,))
        require(
            denied == refused == readonly == direct
            and "feature cut length (depthless extrusion reconstruction is unqualified)" in denied,
            "the ordinary entry points did not uphold the same source boundary",
        )
    require(
        stream.getvalue() == sentinel
        and destination.read_bytes() == sentinel and not unknown.parent.exists()
        and not fresh.parent.exists() and tuple(destination.parent.iterdir()) == (destination,),
        "a rejected conversion mutated its destination or left staging state",
    )
    return {
        "shared_depthless_guard": denied, "existing_destination_preserved": True,
        "uncreated_during_invalid_selection": True, "no_staging_remains": True,
        "other_profile_or_target_refusals": 4, "runtime_input_file_reads": 0,
        "guarded_path_events": dict(guard.events),
    }


def legacy_document(mode):
    from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc
    from interchange.Features.FeatureExtrude import ExtrudeEnd

    if mode == "blind":
        name = "LegacyStockBranchBlind"
        return name, MakePlainDoc(name, 32.75, 16.5, 8.125)
    if mode == "circle":
        from AuthorSdkCircleRequests import make_document
        name = "LegacyStockBranchCircle"
        return name, make_document(
            name, "Front Plane", (5.875, -8.25), 7.375, 21.25,
            "diameter", ExtrudeEnd.KBlind, False, None,
        )
    if mode == "equation":
        return legacy_equation()
    return legacy_import()


def legacy_import():
    from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.Records.RecordConfig import Configuration
    from interchange.Records.RecordSource import CadSource

    points = tuple(PlaneVector(*item) for item in ((1.5, -8.25), (9, -8.25), (9, 8), (1.5, 8)))
    ring = tuple(LineGeometry(a, b) for a, b in zip(points, (*points[1:], points[0]), strict=True))
    solid, *_ = BuildPrism("legacy-analytic-box", Transform(), ring, 10.125, 27.25)
    bare = replace(solid, bodies=(replace(solid.bodies[0], design_body_id=""),))
    document = CadDocument(
        CadSource("kit.neutral", "", ""), (Configuration("active", "Default", True),),
        (), (), (), (), (), (), brep=bare,
    )
    return "LegacyStockBranchImport", document


def legacy_equation():
    from BuildSdkWidthDepth import author_document
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.serialization.EncodeData import ToData
    from tests.Convert.Solidworks.Research.Construction.RectDimensions.MakeRectDimDoc import (
        MakeRectDimDoc,
    )

    name = "LegacyStockBranchEquation"
    document = MakeRectDimDoc(name, False)
    (sketch,) = document.sketches
    (feature,) = document.feature_timeline
    width, height = sketch.parameter_ids
    (depth,) = feature.parameter_ids
    parameters = {value.id: value for value in document.parameters}
    distance = replace(parameters[depth].value, value=parameters[width].value.value / 2)
    entities = tuple(
        replace(value, geometry=LineGeometry(
            PlaneVector(value.geometry.start.x + 27, value.geometry.start.y + 9),
            PlaneVector(value.geometry.end.x + 27, value.geometry.end.y + 9),
        ))
        for value in sketch.entities
    )
    document = replace(
        document, sketches=(replace(sketch, entities=entities),),
        parameters=(parameters[width], parameters[height], replace(parameters[depth], value=distance)),
        feature_timeline=(replace(feature, definition=replace(feature.definition, length=distance)),),
    )
    return name, author_document({
        "document": ToData(document), "equation": {"target": depth, "dependency": width, "divisor": 2},
    })


def legacy_worker(folder, mode):
    from convert import write_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.api.ApiContext import GetRegistry
    from ProveSdkStockWriter import fingerprint
    from VerifySdkCircleEndRegistration import OutputGuard

    name, document = legacy_document(mode)
    filename = name + ".SLDPRT"
    destination = folder / filename
    adapter = GetRegistry().GetWriter(FORMAT)
    guard = OutputGuard(folder, filename)
    sys.addaudithook(guard.audit)
    policy = {"require_native_transfers": True}
    stream = BytesIO()
    with guard.active("memory"):
        require(adapter.supports(document, destination), f"legacy {mode} path was refused")
        if mode != "import":
            require(adapter.supports(document, stream), f"legacy {mode} stream was refused")
            locator = rf"C:\KitSdkCandidates\{filename}"
            streamed = write_document(
                document, stream, destination_format=FORMAT, allow_carrier=False,
                values={**policy, "final_destination": locator},
            )
        else:
            require(not adapter.supports(document, stream), "the path-only import opened a stream")
    with guard.active("path"):
        result = write_document(
            document, destination, destination_format=FORMAT, allow_carrier=False, values=policy,
        )
    payload = destination.read_bytes()
    native = policy_result(result, payload, True, destination)
    if mode != "import":
        require(stream.getvalue() == payload and policy_result(streamed, payload, True, None) == native,
                f"the legacy {mode} stream and path routes differ")
    else:
        require(set(native) == {"brep", "configurations"}, "the imported solid lost its capabilities")
    require("selections" not in native, "a legacy route published a selection claim")
    return {
        "artifact": fingerprint(SldprtArchive.from_bytes(payload).streams, payload),
        "native_transfers": native, "runtime_input_file_reads": 0,
    }


def worker(mode, input_root):
    load_runtime(input_root)
    with TemporaryDirectory(prefix="KitTwoStockRegistrationOutput-") as name:
        folder = Path(name).resolve()
        if mode == "stock":
            return stock_worker(folder)
        if mode == "refusals":
            return refusals_worker(folder)
        return legacy_worker(folder, mode)


def launch(mode, sdk):
    result = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode, "--sdk", str(sdk)),
        input=b"", capture_output=True, timeout=90,
    )
    require(result.returncode == 0, mode + ": " + result.stderr.decode())
    return json.loads(result.stdout)


def prove():
    with TemporaryDirectory(prefix="KitFrozenStockSdk-") as name:
        baseline = Path(name)
        raw = check_output(("git", "archive", FROZEN, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(raw)) as stream:
            stream.extractall(baseline, filter="data")
        base_sdk, current = baseline / "src", ROOT / "src"
        folder = Path("convert/adapters/solidworks/Core/Preparation/TwoStock")
        fixed = {
            str(path.relative_to(base_sdk)): sha256(path.read_bytes()).hexdigest()
            for path in sorted((base_sdk / folder).glob("*.py"))
        }
        require(fixed and all(
            sha256((current / path).read_bytes()).hexdigest() == digest
            for path, digest in fixed.items()
        ), "frozen preparation code has changed")
        positive = launch("stock", current)
        negative = launch("refusals", current)
        controls = {}
        for mode in LEGACY:
            old = launch(mode, base_sdk)
            controls[mode] = launch(mode, current)
            require(controls[mode] == old, f"legacy {mode} route changed")
    return {
        "schema": "kit.sw2026.local-two-stock-registry-candidate.v1",
        "frozen_revision": FROZEN, "frozen_preparer_file_count": len(fixed),
        "source_sha256": {
            path: sha256((ROOT / path).read_bytes()).hexdigest()
            for path in (*PATCHED, str(HERE.relative_to(ROOT)))
        },
        "fresh_processes": 2 + 2 * len(LEGACY), "native_runs": 0, "heldout_inputs_read": 0,
        "registered_candidate": positive, "refusals": negative, "legacy_parity": controls,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=("stock", "refusals", *LEGACY))
    parser.add_argument("--sdk", type=Path)
    args = parser.parse_args()
    print(json.dumps(worker(args.worker, args.sdk) if args.worker else prove(), indent=2))
