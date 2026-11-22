from dataclasses import replace
from math import ulp


BODY_PROOF = "solidworks.native_body"
BODY_STATUS = "solidworks.native_body_names"
CONFIG_STATUS = "solidworks.typed_configuration_graph"
RESOLVED_STATUS = "solidworks.typed_resolved_semantics"


def same_coordinates(original, observed):
    return len(original) == len(observed) and all(
        abs(left - right) <= max(ulp(left), ulp(right))
        for left, right in zip(original, observed, strict=True)
    )


def same_bounds(original, observed):
    def components(bounds):
        low, high = bounds.minimum, bounds.maximum
        return low.x, low.y, low.z, high.x, high.y, high.z

    return same_coordinates(components(original), components(observed))


def check_cache_fallback(original, observed):
    old_body, = original.bodies
    new_body, = observed.bodies
    old_kernel, = original.brep.bodies
    proof = dict(old_body.attributes[BODY_PROOF])
    if tuple(proof[key] for key in (
        "configuration_stream", "partition_stream", "atom_manager_id",
        "body_transmit_index", "body_match_tag", "last_modifying_feature_id",
    )) != ("Contents/Config-0", "Contents/Config-0-Partition", 101, 2, 411, 20):
        raise ValueError("the disclosed circular body's physical owners changed")
    if (proof != original.metadata[BODY_STATUS] or proof != old_kernel.attributes[BODY_PROOF]
            or proof["complete_brep_binding"] is not True
            or old_kernel.design_body_id != old_body.id
            or old_body.provenance is None or old_kernel.provenance != old_body.provenance):
        raise ValueError("the intact circular control lost its actual atom binding")
    owner, partition = old_body.provenance.spans
    if (owner.stream, owner.offset, owner.length, partition.stream) != (
        "Contents/Config-0", 3076, 100, "Contents/Config-0-Partition",
    ):
        raise ValueError("the circular body's atom extent no longer matches the source")
    without_atom = replace(
        old_kernel, design_body_id="", provenance=None,
        attributes={key: value for key, value in old_kernel.attributes.items() if key != BODY_PROOF},
    )
    if (observed.brep != replace(original.brep, bodies=(without_atom,))
            or observed.brep_payloads != original.brep_payloads
            or BODY_STATUS in observed.metadata):
        raise ValueError("rejected configuration changed stored geometry or retained an atom claim")
    original_attrs = {key: value for key, value in old_body.attributes.items() if key != BODY_PROOF}
    if (new_body.name != "Body 1"
            or new_body != replace(
                old_body, name="Body 1", provenance=None,
                attributes={**original_attrs, "native_object_id": None},
                topology=replace(old_body.topology, bounding_box=new_body.topology.bounding_box),
            )
            or not same_bounds(old_body.topology.bounding_box, new_body.topology.bounding_box)):
        raise ValueError("the fallback did not preserve the independent design body summary")


def sketch_drivers(sketch):
    return tuple(
        replace(rule, provenance=None, attributes={})
        for rule in sketch.constraints if rule.driving and rule.parameter_id
    )


def check_retained_profile(original, observed):
    old_sketch, = original.sketches
    new_sketch, = observed.sketches
    old_entities = tuple(value for value in old_sketch.entities if not value.construction)
    new_entities = tuple(value for value in new_sketch.entities if not value.construction)
    (old_circle,) = tuple(value for value in old_entities if value.kind.value == "circle")
    (new_circle,) = new_entities
    old_center, new_center = old_circle.geometry.center, new_circle.geometry.center
    if (not same_coordinates((old_center.x, old_center.y), (new_center.x, new_center.y))
            or old_circle.geometry.radius != new_circle.geometry.radius
            or new_circle != replace(old_circle, geometry=new_circle.geometry, provenance=new_circle.provenance)
            or sketch_drivers(new_sketch) != sketch_drivers(old_sketch)
            or new_sketch != replace(old_sketch, entities=new_sketch.entities, constraints=new_sketch.constraints)):
        raise ValueError("the fallback changed the independently owned circular profile")
    if any(rule.kind == "fixed" for rule in new_sketch.constraints):
        raise ValueError("the fallback claimed a fixed centre without its typed support")


def check_config_fallback(original, observed):
    checked = (CONFIG_STATUS, RESOLVED_STATUS)
    if any(observed.metadata[key]["status"] != "unsupported" for key in checked):
        raise ValueError("the damaged configuration was not reported as unqualified")
    check_cache_fallback(original, observed)
    check_retained_profile(original, observed)
    old_boss = next(step for step in original.feature_timeline if step.id == original.bodies[0].final_feature_id)
    new_boss = next(step for step in observed.feature_timeline if step.id == observed.bodies[0].final_feature_id)
    if (new_boss != replace(old_boss, order=new_boss.order, provenance=new_boss.provenance, attributes=new_boss.attributes)
            or len(original.feature_timeline) != 19 or len(observed.feature_timeline) != 27
            or observed.support_planes != original.support_planes
            or tuple(replace(p, provenance=None, attributes={}) for p in observed.parameters)
            != tuple(replace(p, provenance=None, attributes={}) for p in original.parameters)):
        raise ValueError("the fallback changed the actual boss or its driving dimensions")
