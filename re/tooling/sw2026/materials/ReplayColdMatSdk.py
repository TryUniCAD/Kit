from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from math import isclose
from pathlib import Path
import sys
from traceback import extract_tb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ReplayHeldoutMatSdk import (
    KMatAnchor, KMatCatalog, KModelTint, MEASUREMENT, PUBLIC_AUTHORITY, SLOTS,
    MaterialRecord, PrepMatPart, SldprtAdapter, WriteOptions, guard, native_join, neutral,
    read, require, validate, write_adapter, write_direct, write_registry,
)
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import ReadLength
from convert.adapters.solidworks.Container.Container import SldprtFormatError
from interchange.serialization.JsonCodec import DumpJson, LoadJson


def same(left, right):
    return isclose(left, right, rel_tol=1e-10, abs_tol=1e-10)


def source_model(case, catalog, locator):
    tint = tuple(((KModelTint >> index) & 255) / 255 for index in (0, 8, 16)) + (1.0,)
    material = MaterialRecord("material/assigned-part", catalog[1], catalog[2], tint)
    design = neutral(case, locator, material)
    return replace(
        design, bodies=(replace(design.bodies[0], material_id=material.id),),
        metadata={**design.metadata, KMatCatalog: catalog[0], KMatAnchor: case["kind"]},
    )


def measure_shape(document, case, density):
    body = document.bodies[0]
    topology = body.topology
    require((topology.solid_count, topology.shell_count, topology.face_count,
             topology.edge_count, topology.vertex_count) == (1, 1, 6, 12, 8)
            and topology.valid and document.brep.bodies[0].design_body_id == body.id,
            "strict cold read lost its analytic solid owner")
    extent = [case[key] for key in ("width_m", "height_m", "depth_m")]
    width, height, depth = extent
    require(same(topology.volume * 1e-9, width * height * depth)
            and same(topology.surface_area * 1e-6, 2 * (width * height + width * depth + height * depth))
            and same(topology.volume * 1e-9 * document.materials[0].Density,
                     width * height * depth * density), "strict cold geometry or density changed")
    center = (0.0, 0.0, depth / 2) if case["kind"] == "center" else tuple(value / 2 for value in extent)
    bounds = topology.bounding_box
    for coordinate, expected in zip(("x", "y", "z"), center, strict=True):
        actual = (getattr(bounds.minimum, coordinate) + getattr(bounds.maximum, coordinate)) / 2000.0
        require(same(actual, expected), "strict cold geometry changed its centroid")


def check_design(document, case, catalog, full):
    material, = document.materials
    body, = document.bodies
    sketch, = document.sketches
    feature, = document.feature_timeline
    config, = document.configurations
    kind = case["kind"]
    require((material.name, material.Density, document.metadata[KMatCatalog]) == (catalog[1], catalog[2], catalog[0])
            and body.material_id == material.id and body.final_feature_id == feature.id
            and config.active and config.name == case["configuration"] and feature.sketch_id == sketch.id
            and document.metadata[KMatAnchor] == kind, "strict cold model lost its actual scoped assignment")
    require(len(sketch.closed_profile_entity_ids[0]) == 4
            and sum(entity.construction for entity in sketch.entities) == (1 if kind == "corner" else 4)
            and sum(rule.kind == "coincident" for rule in sketch.constraints) == (1 if kind == "corner" else 3),
            "strict cold model did not retain its actual anchor and construction")
    require([(parameter.name, parameter.owner_id) for parameter in document.parameters]
            == [("D1", sketch.id), ("D2", sketch.id), ("D1", feature.id)]
            and all(same(ReadLength(parameter.value), case[field])
                    for parameter, field in zip(document.parameters, ("width_m", "height_m", "depth_m"), strict=True)),
            "strict cold model changed its actual live drivers")
    require((document.brep is not None) is full and not document.brep_payloads,
            "strict cold geometry selection did not respect the requested mode")
    if full:
        measure_shape(document, case, catalog[2])


def republish(model, payload, options):
    restored = LoadJson(DumpJson(model))
    require(restored == model, "portable cold material design changed after JSON roundtrip")
    for writer in (write_registry, write_direct, write_adapter):
        for source in (model, restored):
            destination = BytesIO()
            result = writer(source, destination, options)
            require(destination.getvalue() == payload and result.vendor_loadable and result.application_usable,
                    "public cold readback emitted different bytes")
    return 6


def refuse_bad(model, payload, options):
    body = model.bodies[0]
    sketch = model.sketches[0]
    bad_models = (
        replace(model, bodies=(replace(body, material_id=None),)),
        replace(model, sketches=(replace(sketch, constraints=sketch.constraints[:-1]),)),
        replace(model, bodies=(replace(body, topology=replace(body.topology, volume=0.0)),)),
        replace(model, source=replace(model.source, sha256="a" * 64)),
    )
    refusals = 0
    for writer in (write_registry, write_direct, write_adapter):
        for bad in bad_models:
            destination = BytesIO()
            try:
                writer(bad, destination, options)
            except (ValueError, NotFoundError):
                require(not destination.getvalue(), "refused cold design changed its destination")
                refusals += 1
            else:
                raise ValueError("writer accepted changed cold material evidence")
    try:
        SldprtAdapter().read(BytesIO(payload), ReadOptions(include_brep=True, strict=True, extract_raw_brep=True))
    except SldprtFormatError:
        return refusals + 1
    raise ValueError("cold material falsely supplied a raw native cache")


def replay(root, slot):
    generation, authority = native_join(root)
    index = SLOTS.index(slot)
    selection, witness = generation["cases"][index], authority["cases"][index]
    exact_report = PUBLIC_AUTHORITY.read_bytes().decode("utf-8")
    require(json.loads(exact_report) == authority, "native material authority differs from its historical control")
    request = read(root, f"Generation/{slot}/Request.json", selection["request_sha256"])
    case, materials, locator = validate(request)
    catalog = materials[case["first_material_key"]]
    denied = guard()
    epoch = request["target"]["saved_at"]
    target = {"final_destination": str(locator)}
    neutral_document = source_model(case, catalog, locator)
    candidate = PrepMatPart(neutral_document, BytesIO(), epoch, WriteOptions(values=target))
    payload = candidate.BytesValue
    require(sha256(payload).hexdigest() == witness["archive_sha256"], "did not reproduce the exact controlled source")
    options = {**target, MEASUREMENT: {"written_at": epoch, "receipt": {"native_report": exact_report}}}
    models = tuple(
        SldprtAdapter().read(BytesIO(payload), ReadOptions(include_brep=full, strict=True))
        for full in (True, False)
    )
    for model, full in zip(models, (True, False), strict=True):
        check_design(model, case, catalog, full)
    writes = sum(republish(model, payload, options) for model in models)
    refusals = refuse_bad(models[0], payload, options)
    require(not denied, "guarded material roundtrip attempted external input")
    return {
        "case": slot, "anchor": case["kind"], "archive_sha256": witness["archive_sha256"],
        "full_and_design_reads": len(models), "exact_public_rewrites": writes,
        "prewrite_and_raw_cache_refusals": refusals,
        "runtime_reads": len(denied), "native_processes_started": 0,
        "physical_body_counts": [1, 1, 6, 12, 8],
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--slot", choices=SLOTS, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(replay(args.root, args.slot), sort_keys=True, allow_nan=False))
    except Exception as exc:
        print(json.dumps({"failure": type(exc).__name__, "frames": [
            (Path(row.filename).name, row.name, row.lineno) for row in extract_tb(exc.__traceback__)
        ]}, sort_keys=True))
        raise SystemExit(1) from None
