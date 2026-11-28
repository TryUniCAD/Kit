from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from math import isclose
from pathlib import Path, PureWindowsPath
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from BuildBakedLabelPair import computed_box
from BuildBakedTolerancePart import EPOCH, ROOT, artifact, checked, encode, model_only, project, require
from ObserveBakedTolerancePart import BUILD, CASES, GUEST
from ProveBakedLocalTolerance import KIND_OWNERS, ring_signature

sys.path.insert(0, str(ROOT / "src"))

from convert import open_document
from convert.Geometry.Parasolid import KMissingParam
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import MakeBareImport
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import MakeLocalPrism
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import KMillimetersPerMeter
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import EncodeLocalBody
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalXmt import EncodeLocalXmt
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from convert.adapters.solidworks.Core.Partition.PartMass import ReadPartMass
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.Preparation.Imports.ImportPartPlan import ImportPartPlan
from convert.adapters.solidworks.Core.Preparation.Imports.MakeImportLight import MakeImportLight
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import PlanImportPart
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector

JOB = "8745548b488001f3de2f4ab309e903da806539c8680e9af8eacc1af5166e5c6a"
NATIVE = "520999b48639661f08019b584e1c9f7faba3349df62383a076ea65b22a9cbd40"
REQUEST_FIELDS = (
    "bounds_mm", "configuration", "feature", "outward_rings", "tolerance_mm",
)


def typed_box(document, tolerance):
    model = document.brep
    return replace(
        document,
        brep=replace(
            model,
            faces=tuple(replace(value, tolerance=tolerance) for value in model.faces),
            edges=tuple(replace(value, tolerance=tolerance) for value in model.edges),
            vertices=tuple(replace(value, tolerance=tolerance) for value in model.vertices),
        ),
    )


def refused(call, expected):
    try:
        call()
    except ValueError as error:
        require(expected in str(error), "unexpected tolerance refusal: " + str(error))
        return str(error)
    raise ValueError("unqualified tolerance unexpectedly composed")


def construct(name, request):
    target = str(PureWindowsPath(GUEST) / "Candidates" / (name + ".SLDPRT"))
    plan = ImportPartPlan(name, request["configuration"], request["feature"])
    recipe = replace(MakePartRecipe(plan, EPOCH), OutputValue=SelfFileInput(target, EPOCH))
    light = MakeImportLight(EPOCH)
    document = computed_box(request["bounds_mm"], request["configuration"])
    rings = json.loads(encode(ring_signature(ReadMassRings(document.brep))))
    require(rings == request["outward_rings"], "box lost the measured outward rings")
    length = request["tolerance_mm"]
    typed = typed_box(document, length)
    plain = MakeBareImport(document, recipe, plan, AmbientValue=light)
    candidate = MakeBareImport(
        typed, recipe, plan, AmbientValue=light, AllowBoxTolerance=True
    )
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    require(
        archive.streams == candidate.StreamsValue
        and archive.streams.keys() == plain.StreamsValue.keys()
        and {k for k, v in archive.streams.items() if v != plain.StreamsValue[k]}
        == {KLocalBodyStream},
        "tolerance changed an unowned stream",
    )
    old = MakeLocalPrism(document.brep)
    current = MakeLocalPrism(typed.brep, AllowBoxTolerance=True)
    expected = length / KMillimetersPerMeter
    for previous, actual in zip(old, current, strict=True):
        if actual.KindValue in KIND_OWNERS:
            require(
                actual.FieldsValue["tolerance"] == expected
                and replace(
                    actual,
                    FieldsValue=dict(actual.FieldsValue, tolerance=KMissingParam),
                ) == previous,
                "tolerance changed another topology field",
            )
        else:
            require(actual == previous, "tolerance changed a different class")
    require(
        EncodeLocalBody(plan.FeatureName, current) == archive.require(KLocalBodyStream),
        "full archive does not own the directly composed kernel",
    )
    transmit = EncodeLocalXmt(current)
    decoded, _ = ReadLocalNodes(transmit)
    require(tuple(decoded.values()) == current, "typed tolerance decode changed a node")
    alternate = MakeBareImport(
        typed_box(document, length * 2), recipe, plan,
        AmbientValue=light, AllowBoxTolerance=True,
    )
    require(
        {k for k, v in alternate.StreamsValue.items() if v != archive.streams[k]}
        == {KLocalBodyStream},
        "changed input tolerance did not drive just its actual native stream",
    )
    return {
        "part": artifact(candidate.BytesValue),
        "baseline_part": artifact(plain.BytesValue),
        "kernel": artifact(transmit),
        "baseline_kernel": artifact(EncodeLocalXmt(old)),
        "alternate_part": artifact(alternate.BytesValue),
        "streams": {key: artifact(value) for key, value in archive.streams.items()},
        "tolerance_m": expected,
        "refusals": {
            "public_selection": refused(
                lambda: PlanImportPart(typed, target), "does not admit local tolerances"
            ),
            "attributed": refused(
                lambda: MakeBareImport(
                    typed, recipe, plan, OwnedBody=True, AllowBoxTolerance=True,
                ),
                "ordinary rectangular solid",
            ),
            "unowned": refused(
                lambda: MakeLocalPrism(document.brep, AllowBoxTolerance=True),
                "positive finite length",
            ),
            "nonuniform": refused(
                lambda: MakeLocalPrism(
                    replace(
                        typed.brep,
                        edges=(replace(typed.brep.edges[0], tolerance=0.0), *typed.brep.edges[1:]),
                    ),
                    AllowBoxTolerance=True,
                ),
                "must agree across all owners",
            ),
        },
    }


def worker(requests):
    require(tuple(requests) == CASES, "disclosed source pair changed")
    for name in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(name)
    with model_only() as accesses:
        cases = {key: construct(key, row) for key, row in requests.items()}
    require(not accesses, "toleranced writer performed runtime access")
    return {"cases": cases, "runtime_external_accesses": len(accesses)}


def saved_case(blob, observed, request):
    doc = open_document(blob, source_format="solidworks.sldprt", strict=True)
    doc.assert_valid()
    require(doc.brep is not None, "strict read did not return stored geometry")
    model = doc.brep
    (body,) = doc.bodies
    (config,) = doc.configurations
    (solid,) = model.bodies
    require(
        body.name == request["feature"]
        and body.final_feature_id == f"sldprt:feature:{observed['feature_id']}"
        and solid.design_body_id == body.id
        and config.active and config.name == request["configuration"],
        "stored geometry lost its feature, name, atom, or configuration",
    )
    geometry = observed["shape"]
    require(
        (len(model.faces), len(model.edges), len(model.vertices))
        == (geometry["faces"], geometry["edges"], geometry["vertices"]),
        "strict saved topology differs from the native solid",
    )
    actual_rings = ring_signature(ReadMassRings(model))
    require(
        all(
            isclose(a, b, rel_tol=0, abs_tol=1e-9)
            for actual, expected in zip(actual_rings, request["outward_rings"], strict=True)
            for first, second in zip(actual, expected, strict=True)
            for a, b in zip(first, second, strict=True)
        ),
        "strict saved loops differ from the actual oriented source",
    )
    tolerance = request["tolerance_mm"]
    require(
        all(isclose(value.tolerance, tolerance, rel_tol=1e-6) for value in model.faces)
        and all(value.tolerance == 0.0 for value in (*model.edges, *model.vertices)),
        "SDK did not retain the stored face and unset edge and vertex values",
    )
    axes = tuple(zip(*(tuple(point) for ring in actual_rings for point in ring), strict=True))
    low = tuple(min(axis) for axis in axes)
    high = tuple(max(axis) for axis in axes)
    bounds = BoundingBox(SpaceVector(*low), SpaceVector(*high))
    mass = ReadPartMass(model, bounds)
    require(mass is not None, "strict saved loops do not measure a closed volume")
    dx, dy, dz = (b - a for a, b in zip(low, high, strict=True))
    area = 2 * (dx * dy + dy * dz + dz * dx)
    actual = (mass.Volume, area, *mass.Centroid, *low, *high)
    expected = (
        geometry["volume_m3"] * KMillimetersPerMeter**3,
        geometry["area_m2"] * KMillimetersPerMeter**2,
        *(
            value * KMillimetersPerMeter
            for value in (*geometry["com_m"], *geometry["bounds_m"][0], *geometry["bounds_m"][1])
        ),
    )
    require(
        all(isclose(a, b, rel_tol=1e-6, abs_tol=1e-9) for a, b in zip(actual, expected, strict=True)),
        "strict saved measures differ from the native rebuilt solid",
    )
    return {
        "archive": artifact(blob),
        "body": body.name,
        "final_feature_id": body.final_feature_id,
        "face_tolerance_mm": model.faces[0].tolerance,
        "unset_edges": len(model.edges),
        "unset_vertices": len(model.vertices),
        "numeric_comparisons": len(actual),
        "oriented_faces": len(actual_rings),
    }


def saved_worker(requests):
    require(tuple(requests) == CASES, "disclosed saved pair changed")
    for name in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le"):
        lookup(name)
    sample = requests[CASES[0]]["source"]
    computed_box(sample["bounds_mm"], sample["configuration"]).assert_valid()
    with model_only() as accesses:
        cases = {
            key: saved_case(b64decode(row["blob"], validate=True), row["native"], row["source"])
            for key, row in requests.items()
        }
    require(not accesses, "resident saved read accessed outside data")
    return {"cases": cases, "runtime_external_accesses": len(accesses)}


def prove(sources, packet):
    job = json.loads(checked(packet / "Job.json", JOB))
    native = json.loads(checked(packet / "Native.json", NATIVE))
    require(
        native["job_sha256"] == JOB
        and native["oracle_build"] == BUILD
        and native["controls_healthy"] and native["passed"],
        "prior native bracket lost its identity or controls",
    )
    projected, live_control, _ = project(sources)
    requests = {}
    for name in CASES:
        request = json.loads(encode(projected[name]))
        baseline = job["cases"][name]
        require(
            all(request[field] == baseline[field] for field in REQUEST_FIELDS)
            and request["source"] == baseline["source"],
            "independent source projection varies from the measured request",
        )
        requests[name] = {field: request[field] for field in REQUEST_FIELDS}
    command = (sys.executable, "-I", "-B", str(HERE), "--worker")
    first, second = (
        subprocess.run(command, input=encode(requests), capture_output=True, check=True)
        for _ in range(2)
    )
    require(first.stdout == second.stdout, "guarded writers disagreed")
    result = json.loads(first.stdout)
    for name, row in result["cases"].items():
        baseline = job["cases"][name]
        require(
            row["part"] == baseline["proof"]["part"]
            and row["kernel"] == baseline["proof"]["kernel"]
            and row["baseline_part"] == baseline["baseline_part"]
            and row["baseline_kernel"] == baseline["baseline_kernel"]
            and row["streams"] == baseline["streams"],
            "direct construction changed the full previously measured product",
        )
    saved = {
        name: {
            "blob": b64encode(
                checked(packet / "Saved" / (name + ".SLDPRT"), native["saves"][name]["sha256"])
            ).decode(),
            "native": native["phases"][name]["rebuilt"],
            "source": request,
        }
        for name, request in requests.items()
    }
    reader = subprocess.run(
        (sys.executable, "-I", "-B", str(HERE), "--saved-worker"),
        input=encode(saved), capture_output=True,
    )
    require(reader.returncode == 0, reader.stderr.decode("utf-8"))
    return {
        "schema": "kit.sw2026.shared-import-box-tolerance.v1",
        "source_files": {name: projected[name]["source"] for name in CASES},
        "rejected_source_control": live_control,
        "previous_native_bracket": {"job_sha256": JOB, "native_sha256": NATIVE, "build": BUILD},
        "guarded_workers": 2,
        "guarded_saved_reader": json.loads(reader.stdout),
        "tool_sha256": sha256(HERE.read_bytes()).hexdigest(),
        "whole_source_conversions": 0,
        "native_processes": 0,
        "heldout_credit": 0,
        **result,
    }


def main():
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--worker", action="store_true")
    modes.add_argument("--saved-worker", action="store_true")
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker or args.saved_worker:
        function = worker if args.worker else saved_worker
        sys.stdout.buffer.write(encode(function(json.load(sys.stdin))))
        return
    require(args.sources and args.packet and args.output, "supply sources, packet, and an unused output")
    report = prove(args.sources, args.packet)
    with args.output.open("xb") as output:
        output.write(encode(report))


if __name__ == "__main__":
    main()
