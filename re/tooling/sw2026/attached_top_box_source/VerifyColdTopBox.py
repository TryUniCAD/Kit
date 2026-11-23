from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from itertools import product
import json
from math import isclose, ulp
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
FORMAT = "solidworks.sldprt"
LOCATOR = r"C:\KitTopCornerHostProbe01\SignedBox.SLDPRT"
EPOCH = 1790000000
CASES = ((20.0, 30.0, 10.0), (17.125, 28.375, 6.625), (17.103, 24.625, 12.25))


def make_document(dimensions):
    from ProveTopCornerPublic import external_anchor
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import LowerBoxModel
    from interchange import CadDocument, CadSource, Configuration, DesignBody, FeatureStep, SupportPlane
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.VectorSpace import SpaceVector

    frame = Transform(
        x_axis=SpaceVector(1, 0, 0),
        y_axis=SpaceVector(0, 0, -1),
        z_axis=SpaceVector(0, 1, 0),
    )
    digest = sha256(json.dumps(dimensions, separators=(",", ":")).encode()).hexdigest()
    seed = CadDocument(
        source=CadSource("kit.neutral.box", "<disclosed-host-probe>", digest),
        configurations=(Configuration("box:default", "Default", active=True),),
        parameters=(),
        support_planes=(SupportPlane("box:top", "XZ-plane", frame),),
        sketches=(),
        selections=(),
        feature_timeline=(FeatureStep("box:boss", "AdditiveBox", "primitive", 0),),
        bodies=(DesignBody("box:body", "Body", "box:boss"),),
        units="mm",
    )
    return external_anchor(LowerBoxModel(
        seed, "SignedBox", ("box:length", "box:width", "box:height"),
        dimensions, ("Length", "Width", "Height"), "Body", TopAttached=True,
    ))


def body_metrics(document, dimensions, projection):
    x, z, y = dimensions
    (body,) = document.bodies
    (boss,) = (row for row in document.feature_timeline if row.id == body.final_feature_id)
    (sketch,) = projection.sketches
    (plane,) = projection.support_planes
    assert body.name == projection.bodies[0].name == "Body"
    assert boss.kind == "extrusion" and boss.operation == "create" and boss.sketch_id == sketch.id
    assert len(document.feature_timeline) == 19 and plane.name == "Top Plane" and boss.definition.reversed
    assert len(sketch.entities) == 5 and sketch.entities[-1].fixed and sketch.entities[-1].construction
    (origin,) = (row for row in sketch.constraints if row.kind == "coincident")
    assert origin.driving and not origin.suppressed and origin.references[0].entity_id == sketch.entities[-1].id
    assert (body.topology.solid_count, body.topology.shell_count, body.topology.face_count,
            body.topology.edge_count, body.topology.vertex_count) == (1, 1, 6, 12, 8)
    assert isclose(body.topology.volume, x * y * z, rel_tol=1e-12)
    assert isclose(body.topology.surface_area, 2 * (x * y + y * z + x * z), rel_tol=1e-12)
    (shape_body,) = document.brep.bodies
    assert shape_body.design_body_id == body.id
    points = tuple((row.point.x, row.point.y, row.point.z) for row in document.brep.vertices)
    expected = tuple(product((0.0, x), (-y, 0.0), (0.0, z)))
    assert all(sum(all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
                       for a, b in zip(point, wanted, strict=True))
                   for point in points) == 1 for wanted in expected)
    center = tuple(sum(coords) / len(points) for coords in zip(*points, strict=True))
    assert all(isclose(actual, expected, rel_tol=1e-12) for actual, expected in
               zip(center, (x / 2, -y / 2, z / 2), strict=True))
    public = {row.name: row.value.value for row in document.parameters}
    assert set(public) == {"Length", "Width", "Height"}
    for name, value in zip(("Length", "Width", "Height"), dimensions, strict=True):
        assert abs(public[name] - value) <= max(ulp(public[name]), ulp(value))
    input_values = {row.name: row for row in projection.parameters}
    assert input_values["Length"].owner_id == input_values["Width"].owner_id == sketch.id
    assert input_values["Height"].owner_id == boss.id
    assert input_values["Length"].value.value.hex() == (x * 0.001).hex()
    assert input_values["Width"].value.value.hex() == (z * 0.001).hex()
    return {"topology": [1, 1, 6, 12, 8], "feature_rows": 19,
            "active_origin_coincidence": True, "named_drivers": len(public),
            "length_readback_ulps": abs(public["Length"] - x) / ulp(x),
            "independent_signed_center_check": True}


def refusal(operation, expected):
    try:
        operation()
    except (ValueError, TypeError) as error:
        if expected not in str(error):
            raise
    else:
        raise ValueError("unexpected accepted request")


def negative_controls(native, design, document, writer, settings):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Readback.PrepColdTop import PrepColdTop

    (sketch,) = native.sketches
    (body,) = native.bodies
    relation = sketch.constraints[-1]
    bad_origin = replace(relation, references=(relation.references[0], replace(relation.references[1], point="end")))
    first, *rest = native.parameters
    refuted = (
        (design, "full cache-free source"),
        (replace(native, bodies=(replace(body, name="Other body"),)), "differs from its regenerated part"),
        (replace(native, metadata={**native.metadata, "unexpected_property": True}), "differs from its regenerated part"),
        (replace(native, sketches=(replace(sketch, constraints=(*sketch.constraints[:-1], bad_origin)),)),
         "actual starting corner"),
        (replace(native, parameters=(replace(first, owner_id=body.final_feature_id), *rest)), "owned sketch length"),
    )
    untouched = BytesIO(b"unmodified stream")
    for variant, message in refuted:
        refusal(lambda: PrepColdTop(variant, untouched, EPOCH, settings), message)
    refusal(lambda: PrepColdTop(native, untouched, EPOCH + 1, settings), "differs from its regenerated part")
    moved = WriteOptions(values={"final_destination": r"C:\KitTopCornerHostProbe02\SignedBox.SLDPRT"})
    refusal(lambda: PrepColdTop(native, untouched, EPOCH, moved), "differs from its regenerated part")
    refusal(lambda: writer.write(document, untouched, settings), "offline native measurement receipt")
    refusal(lambda: write_document(document, untouched, destination_format=FORMAT,
                                   allow_carrier=False, values=settings.values), "offline native measurement receipt")
    assert untouched.getvalue() == b"unmodified stream" and untouched.tell() == 0
    return len(refuted) + 4


def worker(case):
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE.parent.parent)]
    from ProveTopCornerPublic import warm
    from VerifySdkCircleEndRegistration import OutputGuard
    from convert import open_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Readback.PrepColdTop import PrepColdTop
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Readback.ReadTopInput import ReadTopInput
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.api.ApiContext import GetRegistry

    document = make_document(CASES[case])
    document.assert_valid()
    warm()
    writer = GetRegistry().GetWriter(FORMAT)
    guard = OutputGuard(ROOT, "SignedBox.SLDPRT")
    sys.addaudithook(guard.audit)
    settings = WriteOptions(values={"final_destination": LOCATOR, "require_native_transfers": True})
    with guard.active("memory"):
        original = PrepareNative(document, BytesIO(), EPOCH, settings).BytesValue
        native = open_document(original, source_format=FORMAT, strict=True)
        design = open_document(original, source_format=FORMAT, strict=True, include_brep=False)
        projected = ReadTopInput(native, "SignedBox")
        recreated = PrepColdTop(native, BytesIO(), EPOCH, settings).BytesValue
        assert recreated == original
        metrics = body_metrics(native, CASES[case], projected)
        assert design.brep is None and design.bodies[0].name == "Solid Bodies"
        assert design.parameters == native.parameters
        refusals = negative_controls(native, design, document, writer, settings)
    streams = SldprtArchive.from_bytes(recreated).streams
    assert len(streams) == 10 and not guard.denied
    return {"bytes": len(recreated), "sha256": sha256(recreated).hexdigest(),
            "streams": {name: {"bytes": len(value), "sha256": sha256(value).hexdigest()}
                        for name, value in sorted(streams.items())},
            "metrics": metrics, "refusals_before_output": refusals,
            "runtime_input_file_reads": len(guard.denied)}


def source_manifest():
    namespace = "src/convert/adapters/solidworks/Core/Preparation/"
    proof_paths = [
        HERE.relative_to(ROOT).as_posix(),
        namespace + "PrepareNative.py",
        namespace + "Equations/ReadEqSketch.py",
        namespace + "Readback/CheckColdRead.py",
        namespace + "FreecadBox/PlanTopCorner.py",
        *[namespace + "FreecadBox/Readback/" + name
          for name in ("PrepColdTop.py", "ReadTopDims.py", "ReadTopInput.py")],
    ]
    return {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in proof_paths}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", type=int, choices=range(len(CASES)))
    arguments = parser.parse_args()
    if arguments.worker is not None:
        print(json.dumps(worker(arguments.worker), sort_keys=True))
        return
    results = {}
    for case in range(len(CASES)):
        child = run((sys.executable, "-I", "-B", str(HERE), "--worker", str(case)),
                    check=True, capture_output=True, timeout=90)
        if child.stderr:
            raise ValueError(child.stderr.decode(errors="replace"))
        results[str(case + 1)] = json.loads(child.stdout)
    assert len({row["sha256"] for row in results.values()}) == len(CASES)
    assert results["3"]["metrics"]["length_readback_ulps"] == 1.0
    print(json.dumps({"schema": "kit.sw2026.cold-top-box-reconstruction.v1",
                      "cases": results, "guarded_workers": len(results),
                      "source_manifest_sha256": source_manifest(),
                      "new_native_oracle_launches": 0, "benchmark_conversion_credits": 0},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
