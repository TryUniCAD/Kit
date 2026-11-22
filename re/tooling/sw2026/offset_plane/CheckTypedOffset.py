from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from math import isclose, pi
from pathlib import Path
from subprocess import run
import sys

CHECKOUT = Path(__file__).resolve().parents[4]
CASES = (
    (
        "01",
        "FrontOffsetCircle",
        "d7c22522f52c67e29a6874f29f1ba610d4fa1515de63a6c3a509ed28636375eb",
        "9a565b31ab2fcb750f993ab3e7249316f1437712aed879445f2a3986b72d922e",
        "381ec5033f864322f457ca82fd1f1ffef5e4dc953a5dd00fd4567621a06fd2d1",
    ),
    (
        "03",
        "TopReverseOffset",
        "56414188a4535df0b6e10d081869beda53c469634499809ef202611e56a69dfd",
        "732d0d93db968c2f26242dbb92dcfa75d3a9748938d35ef7d602caacb1977a85",
        "a3badc21c75925ac2f40290be7a5ef4b1fd3d5fa1f9dbec926fa6d92f73513b1",
    ),
    (
        "04",
        "RightOffsetCircle",
        "735cd1fd376fb9ff4efbb54f7af75af976d727c52c2d25b1392b2d0ed0380d5b",
        "8cd21b6d7d1be689f120cce89ee2a968dbf55ca016cc9354b3dcd242f795a297",
        "51ab991098c9e7cf46844f6e84017847b5151d919bbd8f98491e149a3c097015",
    ),
)
METHOD_HASH = "69d26121c617641841dd29bd43867f082ae59d32a68cf5ace03903e11781cd3a"
ORACLE_HASH = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"


def digest(data):
    return sha256(data).hexdigest()


def checked(path, expected):
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"disclosed input digest differs: {path.name}")
    return data


def check_neutral(data, request):
    from convert import open_document
    from interchange.Features.FeatureKinds import RefPlaneFeature

    document = request["document"]
    offset = request["offset_plane_discovery"]
    axis = "xyz".index(document["plane_axis"])
    amount = (offset["distance_m"] / 0.001) * (-1 if offset["reverse"] else 1)
    radius = document["radius_m"] * 1000
    depth = document["depth_m"] / 0.001
    origin = [0.0, 0.0, 0.0]
    origin[axis] = amount
    centroid = origin.copy()
    centroid[axis] += depth / 2
    full = open_document(data, source_format="solidworks.sldprt", strict=True)
    design = open_document(
        data, source_format="solidworks.sldprt", strict=True, include_brep=False
    )
    for read in (full, design):
        read.assert_valid()
        assert len(read.parameters) == 3 and len(read.feature_timeline) == 20
        parameters = {item.id: item for item in read.parameters}
        support = next(
            plane for plane in read.support_planes if plane.name == offset["name"]
        )
        base = next(
            plane
            for plane in read.support_planes
            if plane.name
            == request["presentation"]["plane_names"][document["plane_axis"]]
        )
        feature = next(
            step for step in read.feature_timeline if step.name == support.name
        )
        sketchstep = next(
            step
            for step in read.feature_timeline
            if step.name == document["sketch_name"]
        )
        boss = next(
            step
            for step in read.feature_timeline
            if step.name == document["extrusion_name"]
        )
        (sketch,) = read.sketches
        assert type(feature.definition) is RefPlaneFeature
        assert (
            feature.definition.support_plane_id == sketch.support_plane_id == support.id
        )
        assert feature.definition.reference_plane_id == base.id
        assert feature.input_feature_ids == (
            next(step.id for step in read.feature_timeline if step.name == base.name),
        )
        assert sketchstep.input_feature_ids == (
            feature.id,
        ) and boss.input_feature_ids == (sketchstep.id,)
        assert feature.order < sketchstep.order < boss.order
        assert (
            feature.definition.offset.value == amount
            and support.offset_parameter_id in feature.parameter_ids
        )
        assert sketched_circle(sketch)
        assert tuple((rule.kind, rule.parameter_id) for rule in sketch.constraints) == (
            ("radius", sketchstep.parameter_ids[0]), ("fixed", None)
        )
        assert all(
            isclose(value, wanted, abs_tol=1e-10)
            for value, wanted in zip(
                vector(support.transform.origin), origin, strict=True
            )
        )
        owners = []
        for step, expected in (
            (feature, abs(amount)),
            (sketchstep, radius),
            (boss, depth),
        ):
            (identifier,) = step.parameter_ids
            parameter = parameters[identifier]
            owner = parameter.attributes["typed_archive_owner"]
            assert parameter.name == "D1" and isclose(
                parameter.value.value, expected, abs_tol=1e-10
            )
            owners.append(owner)
        assert owners[0]["slot"] == "f6f8.f98" and owners[2]["slot"] == "f818.f18"
        assert len({owner["object_index"] for owner in owners}) == 3
    assert full.brep is not None and design.brep is None
    (body,) = full.bodies
    topology = body.topology
    assert (
        topology.solid_count,
        topology.shell_count,
        topology.face_count,
        topology.edge_count,
        topology.vertex_count,
    ) == (1, 1, 3, 2, 2)
    assert isclose(topology.volume, pi * radius**2 * depth, rel_tol=1e-12)
    assert isclose(
        topology.surface_area, 2 * pi * radius * (radius + depth), rel_tol=1e-12
    )
    bounds = topology.bounding_box
    assert bounds is not None
    reconstructed_centroid = tuple(
        (value + other) / 2
        for value, other in zip(
            vector(bounds.minimum), vector(bounds.maximum), strict=True
        )
    )
    assert all(
        isclose(value, wanted, abs_tol=1e-10)
        for value, wanted in zip(reconstructed_centroid, centroid, strict=True)
    )
    return {
        "signed_offset_mm": amount,
        "driver_owner_indices": [owner["object_index"] for owner in owners],
        "volume_mm3": topology.volume,
        "area_mm2": topology.surface_area,
        "centroid_mm": reconstructed_centroid,
        "faces": topology.face_count,
        "ordered_neutral_features": len(full.feature_timeline),
        "strict_read_modes": 2,
    }


def vector(value):
    return value.x, value.y, value.z


def sketched_circle(sketch):
    from interchange.geometry.Models.GeometryCurves import (
        CircleGeometry,
        PointGeometry,
    )

    circle, center = sketch.entities
    return (
        type(circle.geometry) is CircleGeometry
        and type(center.geometry) is PointGeometry
        and circle.geometry.center == center.geometry.point
        and circle.geometry.center.x == circle.geometry.center.y == 0
        and sketch.constraints[1].references[0].entity_id == center.id
    )


def check_linked(data):
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )

    archive = SldprtArchive.FromBytes(data)
    linked = ReadNativeLink(archive, 0)
    config, resolved = linked.ConfigValue, linked.ResolvedValue
    assert WriteConfigMut(config.RootValue, 19000, config.HeaderValue)[
        0
    ] == archive.require(linked.ConfigName)
    assert WriteResolMut(
        resolved.RootsValue,
        resolved.ExtraFields,
        19000,
        config.MapValue,
        resolved.ContextValue,
    )[0] == archive.require(linked.StreamName)
    return {
        "configuration_map_counter": config.MapValue.CounterValue,
        "resolved_map_counter": resolved.MapValue.CounterValue,
    }


def check_refusals(candidate):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt
    from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
    from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat

    plane = next(
        node
        for node in candidate.ResolvedValue.RootsValue
        if node is not None
        and node.ClassValue.NameValue == "moRefPlane_c"
        and node.FieldsValue["f6f8"].ClassValue.NameValue == "moFaceRefPlnData_c"
    )
    fields = plane.FieldsValue["f6f8"].FieldsValue
    wrapper = fields["f90"]["f58"].FieldsValue["ff0"]
    sketch = candidate.ProfileValue.ReferenceValue.FieldsValue["ff0"]
    parameter = (
        fields["f98"]
        .FieldsValue["f850"][0]["o"]
        .FieldsValue["ff0"]
        .FieldsValue["f28"]
        .FieldsValue
    )
    changes = (
        (wrapper, "f00", plane.FieldsValue["f08"], "expected concrete moDefaultRefPlnData_c"),
        (sketch, "f00", wrapper["f00"], "mismatched local selection owner"),
        (
            parameter,
            "f58",
            parameter["f58"] * 1.5,
            "state contradicts the linked distance",
        ),
    )
    result = []
    for owner, field, changed, expected in changes:
        old = owner[field]
        owner[field] = changed
        try:
            resolved, _ = WriteResolMut(
                candidate.ResolvedValue.RootsValue,
                None,
                19000,
                candidate.ConfigValue.MapValue,
                candidate.ResolvedValue.ContextValue,
            )
        finally:
            owner[field] = old
        data = BuildSldprt(
            {**candidate.StreamsValue, KResolvedFeaturesStream: resolved},
            FormatVersion=4,
        )
        for include in (True, False):
            try:
                open_document(
                    data,
                    source_format="solidworks.sldprt",
                    strict=True,
                    include_brep=include,
                )
            except SldprtFormat as error:
                if expected not in str(error):
                    raise
            else:
                raise ValueError(f"contradictory typed {field} was accepted")
        result.append(expected)
    return result


def worker(request):
    sys.path.insert(0, str(CHECKOUT / "src"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from CheckScopedPlainWriter import WriterAudit
    from DisclosedOffsetRequest import prepare_disclosed
    from convert import open_document
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from interchange.Features.FeatureKinds import RefPlaneFeature

    for module_name in (
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module_name)
    for encoding in ("utf-8", "utf-16-le", "latin-1", "ascii"):
        lookup(encoding)
    audit = WriterAudit(CHECKOUT / "src", CHECKOUT / "unused-offset-datum.SLDPRT")
    sys.addaudithook(audit.observe)
    audit.phase = "write"
    candidate = prepare_disclosed(request)
    audit.phase = "done"
    expect = candidate.BytesValue
    read = check_neutral(expect, request)
    replay = check_linked(expect)
    refusals = check_refusals(candidate)
    if (
        audit.denied
        or audit.target_opens
        or any(
            name in sys.modules
            for name in ("pythoncom", "win32com.client", "FreeCAD", "adsk")
        )
    ):
        raise ValueError("isolated writer crossed its runtime boundary")
    return {
        "bytes": len(expect),
        "sha256": digest(expect),
        "streams": {
            name: {"bytes": len(data), "sha256": digest(data)}
            for name, data in candidate.StreamsValue.items()
        },
        "runtime_input_file_reads": len(audit.denied),
        "geometry": read,
        "linked_replay": replay,
        "malformed_input_refusals": refusals,
    }


def native_observation(path, expected_hash, case):
    result = loads(checked(path, expected_hash))
    phases = result["phases"]
    assert [phase["role"] for phase in phases] == [
        "ControlBefore",
        "Generated",
        "Reopen",
        "ControlAfter",
    ]
    assert all(
        result[key] is True
        for key in (
            "passed",
            "controls_healthy",
            "source_generated_paired_acceptance",
            "generated_initial_edit_tree_equal",
            "generated_edit_reopen_tree_equal",
            "immutable_inputs_unchanged",
            "native_phases_distinct_and_ordered",
        )
    )
    assert result["heldout_inputs_read"] == 0 and result["distinct_processes"] == 4
    process_keys = {
        (
            phase["oracle_identity"]["process_id"],
            phase["oracle_identity"]["process_creation_filetime"],
        )
        for phase in phases
    }
    assert len(process_keys) == 4
    for phase in phases:
        identity = phase["oracle_identity"]
        assert (
            identity["file_version"] == "34.5.2.0604"
            and identity["sha256"] == ORACLE_HASH
        )
        assert (
            phase["passed"] is True
            and phase["open_errors"] == phase["open_warnings"] == 0
        )
        assert phase["initial_body_count"] == 1
    paired = result["source_generated_identity"]
    assert (
        paired["passed"] and paired["source_nodes"] == paired["generated_nodes"] == 26
    )
    assert not paired["tree_differences"] and all(paired["checks"].values())
    assert case["native_result_sha256"] == expected_hash
    return {
        "result_sha256": expected_hash,
        "complete_native_feature_rows": 26,
        "native_processes": len(process_keys),
        "numeric_checks": case["numeric_checks"],
        "controls_healthy": True,
    }


def invoke(data):
    process = run(
        [sys.executable, "-I", "-B", __file__, "--worker"],
        input=data,
        capture_output=True,
    )
    if process.returncode:
        raise RuntimeError(process.stderr.decode())
    return loads(process.stdout)


def check_all(disclosure, method_path):
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    method = loads(checked(method_path, METHOD_HASH))
    output = []
    for (suffix, name, req_hash, file_hash, native_hash), method_row in zip(
        CASES, method["disclosed_native_cases"], strict=True
    ):
        case = disclosure / f"GeneratedReferencePlaneParity{suffix}"
        data = checked(case / "Request.json", req_hash)
        first, second = invoke(data), invoke(data)
        reference = checked(case / "FrozenGenerated" / (name + ".SLDPRT"), file_hash)
        streams = SldprtArchive.FromBytes(reference).streams
        assert (
            first == second
            and first["sha256"] == file_hash == method_row["generated_sha256"]
        )
        assert first["streams"] == {
            key: {"bytes": len(value), "sha256": digest(value)}
            for key, value in streams.items()
        }
        output.append(
            {
                "case": name,
                "request_sha256": req_hash,
                "guarded_builds": 2,
                **first,
                "native": native_observation(
                    case / "Inspection" / "PairedReferencePlaneResults.json",
                    native_hash,
                    method_row,
                ),
            }
        )
    changed = deepcopy(
        loads(
            checked(
                disclosure / "GeneratedReferencePlaneParity04" / "Request.json",
                CASES[2][2],
            )
        )
    )
    changed["offset_plane_discovery"]["distance_m"] *= 1.25
    changed["document"]["circle_dimension"]["text_point_m"][0] = changed[
        "offset_plane_discovery"
    ]["distance_m"]
    alternate = invoke(dumps(changed).encode())
    assert alternate["sha256"] != output[2]["sha256"]
    assert alternate["geometry"]["volume_mm3"] == output[2]["geometry"]["volume_mm3"]
    return {
        "schema": "kit.sw2026.typed-offset-datum-evidence.v1",
        "method_sha256": METHOD_HASH,
        "cases": output,
        "model_variation": alternate,
        "new_native_processes": 0,
        "heldout_payloads_read": 0,
        "worker_sha256": digest(Path(__file__).read_bytes()),
        "request_translator_sha256": digest(
            Path(__file__).with_name("DisclosedOffsetRequest.py").read_bytes()
        ),
    }


def main():
    tool = ArgumentParser()
    tool.add_argument("--worker", action="store_true")
    tool.add_argument("--disclosure", type=Path)
    tool.add_argument("--native-method", type=Path)
    args = tool.parse_args()
    if args.worker:
        print(dumps(worker(loads(sys.stdin.buffer.read())), sort_keys=True))
    else:
        sys.path.insert(0, str(CHECKOUT / "src"))
        print(
            dumps(
                check_all(args.disclosure, args.native_method), sort_keys=True, indent=2
            )
        )


if __name__ == "__main__":
    main()
