from dataclasses import replace
from hashlib import sha256
import json

from convert import extract_brep, open_document
from convert.Geometry.Parasolid import ReadBrepResult
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Core.Partition.Current.ReadActiveModel import ReadActiveModel

from FixtureGeometry import check_geometry


def document_hash(document):
    return sha256(document.to_json().encode()).hexdigest()


def payload_rows(document):
    return [(item.source_stream, item.kind, item.schema, item.sha256, item.data)
            for item in document.brep_payloads]


def check_case(root, case, output):
    path = root / case["path"]
    original = path.read_bytes()
    assert sha256(original).hexdigest() == case["sha256"]
    full = open_document(original, source_format="solidworks.sldprt", strict=True)
    no_tess = open_document(original, source_format="solidworks.sldprt", strict=True,
                            include_brep=True, include_tessellation=False)
    assert full.to_json() == no_tess.to_json(), case["role"]
    geometry = check_geometry(full, case)
    configuration, = (item for item in full.configurations if item.active)
    config_id = configuration.attributes["native_configuration_id"]
    stream = f"Contents/Config-{config_id}-Partition"
    archive = SldprtArchive.from_bytes(original, case["role"])
    native = DecodePartition(archive.Require(stream), stream)
    active, = (item for item in native if item.kind == "partition")
    legacy, reason = ReadBrepResult(active.data)
    if case["role"] == "FiveLine":
        assert legacy is None and reason == "invalid partition topology (missing vertex point)"
    else:
        assert legacy is not None, (case["role"], reason)
        assert ReadActiveModel(active.data) == legacy, case["role"]
        if case["role"] not in ("OneLight", "Legacy"):
            body, = legacy.bodies
            public_body, = full.bodies
            bound, = full.brep.bodies
            assert set(bound.attributes).issubset({"solidworks.native_body"})
            if bound.provenance is not None:
                assert bound.provenance.adapter == "solidworks.sldprt"
                assert any(span.stream == stream and span.offset == 0 and span.length == len(archive.Require(stream))
                           for span in bound.provenance.spans)
            if bound.attributes:
                ownership = bound.attributes["solidworks.native_body"]
                assert ownership["complete_brep_binding"] is True and ownership["partition_stream"] == stream
                assert ownership["body_count"] == 1
            aligned = replace(legacy, bodies=(replace(body, design_body_id=public_body.id,
                                                      provenance=bound.provenance, attributes=bound.attributes),))
            assert aligned == full.brep, case["role"]
    for item in full.brep_payloads:
        assert item.data is not None and sha256(item.data).hexdigest() == item.sha256
    retained = [item for item in full.brep_payloads if item.source_stream == stream]
    assert [(item.kind, item.schema, item.sha256, item.data) for item in retained] == [
        (item.kind, item.schema, item.sha256, item.data) for item in native]
    design = open_document(original, source_format="solidworks.sldprt", strict=True,
                           include_brep=False, include_tessellation=False)
    assert design.brep is None and not design.brep_payloads and not design.meshes
    assert design.parameters == full.parameters and design.sketches == full.sketches, case["role"]
    assert design.feature_timeline == full.feature_timeline, case["role"]
    assert design.configurations == full.configurations and design.support_planes == full.support_planes, case["role"]
    extracted = extract_brep(original, output / case["role"], source_format="solidworks.sldprt")
    assert [file.read_bytes() for file in extracted] == [item.data for item in full.brep_payloads], case["role"]
    assert path.read_bytes() == original
    result = {"input_sha256": case["sha256"], "geometry": geometry,
              "default_document_sha256": document_hash(full), "model_only_document_sha256": document_hash(design),
              "raw_payload_count": len(full.brep_payloads), "legacy_reason": reason,
              "legacy_success_preserved": legacy is not None,
              "full_public_binding_compared": case["role"] not in ("OneLight", "Legacy", "FiveLine"),
              "model_only_preserved": True, "raw_preserved": True,
              "diagnostics": sorted({item.code for item in full.diagnostics})}
    if case["producer"] == "kit":
        recipe = root / "re/solidworks/Fixtures/PartitionVertices" / case["recipe"]
        recipe_raw = recipe.read_bytes()
        assert sha256(recipe_raw).hexdigest() == case["recipe_sha256"]
        request = json.loads(recipe_raw)
        depth = request["document"]["parameters"]["$tuple"][0]["value"]["value"]
        driver, = full.parameters
        assert driver.attributes["native_value"].hex() == depth.hex()
        assert recipe.read_bytes() == recipe_raw
    return result
