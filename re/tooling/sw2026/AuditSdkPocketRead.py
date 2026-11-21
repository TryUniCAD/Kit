from hashlib import sha256
from json import dumps, load
from math import isclose
from pathlib import Path
import os
import sys


ROOT = Path(sys.argv[1]).resolve(strict=True)
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from convert import open_document
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange import CircleGeometry, ExtrusionFeature, PointGeometry


def require(value, message):
    if not value:
        raise ValueError(message)


def alter(payload, fault):
    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0)
    boss, cut = link.ResolvedValue.RootsValue[-3], link.ResolvedValue.RootsValue[-1]
    fields = cut.FieldsValue
    if fault == "consumes-output":
        fields["f530"] = fields["f528"]
    elif fault == "chooser-owner":
        fields["f4c0"]["f68"] = boss
    elif fault == "bad-scope":
        fields["f544"] = 2
    elif fault == "wrapper-atom":
        fields["f548"]["items"][0]["o"].FieldsValue["f18"] = 1
    elif fault == "cold-selection":
        fields["f544"] = 1
    elif fault == "extra-end":
        fields["f818"].FieldsValue["f20"] = boss.FieldsValue["f818"].FieldsValue["f18"]
    else:
        raise ValueError("unrecognized cut ownership fault")
    resolved, _ = WriteResolMut(
        link.ResolvedValue.RootsValue,
        link.ResolvedValue.ExtraFields,
        19000,
        link.ConfigValue.MapValue,
        link.ResolvedValue.ContextValue,
    )
    streams = {row.name: row.data for row in archive.records}
    streams[link.StreamName] = resolved
    return BuildSldprt(streams, FormatVersion=4)


def check_document(document, expected):
    document.assert_valid()
    graph = document.metadata["solidworks.typed_resolved_semantics"]
    require(graph["status"] == "supplemented", str(graph.get("diagnostic")))
    evidence = graph["cut_body_dependency"]
    require(evidence["binding"] == expected["binding"]
            and evidence["feature_scope_code"] == expected["scope"], "unexpected body linkage or archive scope")
    if expected["binding"] == "saved_configuration_atom_alias":
        require(evidence["consumed_atom_id"] > 0 and evidence["result_atom_id"] > 0
                and evidence["consumed_atom_id"] != evidence["result_atom_id"], "saved atom identities are absent or conflated")
    else:
        require("consumed_atom_id" not in evidence and "result_atom_id" not in evidence, "cold read supplied unstored atom identities")
    features = [row for row in document.feature_timeline if isinstance(row.definition, ExtrusionFeature)]
    require(len(features) == 2, "the public feature history does not contain both extrusions")
    boss, cut = features
    require(boss.id == f"sldprt:feature:{evidence['producer_feature_id']}"
            and cut.id == f"sldprt:feature:{evidence['consumer_feature_id']}"
            and tuple(str(row.operation) for row in features) == ("join", "cut"), "actual boss and cut ownership changed")
    boss_owner, cut_owner = graph["extrusions"]
    for feature, owner, depth in zip(features, (boss_owner, cut_owner),
                                    (expected["boss_depth_mm"], expected["cut_depth_mm"]), strict=True):
        expected_inputs = tuple(f"sldprt:feature:{key}" for key in owner["parent_ids"])
        (driver,) = [p for p in document.parameters if p.owner_id == feature.id and p.id in feature.parameter_ids]
        require(feature.input_feature_ids == expected_inputs
                and str(feature.definition.end_condition) == "blind"
                and feature.definition.reversed is (feature is cut)
                and isclose(feature.definition.length.value, depth, abs_tol=1e-9)
                and driver.value == feature.definition.length and driver.role.value == "driving"
                and driver.attributes["typed_archive_owner"]["value_field"] == "f58", "live depth or typed parent ownership changed")
    require(cut.input_feature_ids == (boss.id, f"sldprt:feature:{cut_owner['profile_id']}")
            and document.bodies[0].final_feature_id == cut.id, "cut lost its body producer, profile or final body")
    sketch = next(row for row in document.sketches if row.id == cut.sketch_id)
    (entity,) = [row for row in sketch.entities if isinstance(row.geometry, CircleGeometry)]
    circle = entity.geometry
    require(sketch.closed_profile_entity_ids == ((entity.id,),), "cut does not own one closed circle")
    center = expected["center_mm"]
    require(all(isclose(value, reference, abs_tol=1e-9)
                for value, reference in zip((circle.center.x, circle.center.y, circle.radius),
                                            (*center, expected["radius_mm"]), strict=True)), "actual circular contour changed")
    radial = expected["radial_mode"]
    kinds = {str(row.kind) for row in sketch.constraints}
    require(kinds == ({radial, "fixed"} if radial else set()), "free or driven circle relations changed")
    if radial:
        (rule,) = [row for row in sketch.constraints if str(row.kind) == radial]
        (param,) = [p for p in document.parameters if p.id == rule.parameter_id]
        require(param.role.value == "driving" and param.id in sketch.parameter_ids
                and param.owner_id == f"sldprt:feature:{cut_owner['profile_id']}"
                and isclose(param.value.value, circle.radius * (2 if radial == "diameter" else 1), abs_tol=1e-9)
                and rule.references[0].entity_id == entity.id, "the radial driver lost its real circle owner")
        (fix,) = [row for row in sketch.constraints if str(row.kind) == "fixed"]
        (center_ref,) = fix.references
        center_entity = next(row for row in sketch.entities if row.id == center_ref.entity_id)
        require(fix.parameter_id is None and
                ((center_entity is entity and center_ref.point == "center")
                 or (isinstance(center_entity.geometry, PointGeometry)
                     and center_entity.geometry.point == circle.center)),
                "the fixed relation lost its real centre owner")
    else:
        (center_entity,) = [row for row in sketch.entities if isinstance(row.geometry, PointGeometry)]
        require(center_entity.geometry.point == circle.center
                and cut_owner["profile_id"] in graph["free_circle_profiles"], "free circle lost its actual centre")
    return {"body_link": dict(evidence), "boss_depth_mm": boss.definition.length.value,
            "cut_depth_mm": cut.definition.length.value, "radial_mode": radial,
            "feature_count": len(document.feature_timeline), "cut_parent_count": len(cut.input_feature_ids)}


def main(request):
    path = Path(request["path"])
    payload = path.read_bytes()
    digest = sha256(payload).hexdigest()
    require(digest == request["source_sha256"], "source file does not match its lock")
    fault = request.get("fault")
    mode = request["mode"]
    require(mode in ("path", "bytes"), "expected path or byte public read")
    actual = alter(payload, fault) if fault else payload
    source = path if mode == "path" and fault is None else actual
    document = open_document(source, source_format="solidworks.sldprt", strict=True,
                             include_brep=False, include_tessellation=False)
    if fault:
        graph = document.metadata["solidworks.typed_resolved_semantics"]
        require(graph["status"] == "unsupported" and "cut_body_dependency" not in graph
                and request["diagnostic"] in graph["diagnostic"], "fault acquired authoritative typed ownership")
        result = {"fault": fault, "typed_link_rejected": True, "diagnostic": graph["diagnostic"]}
    else:
        result = check_document(document, request["expectation"])
    return {"passed": True, "process_id": os.getpid(), "source_sha256": digest, "mode": mode,
            "read_sha256": sha256(actual).hexdigest(), **result}


if __name__ == "__main__":
    print(dumps(main(load(sys.stdin)), sort_keys=True, allow_nan=False))
