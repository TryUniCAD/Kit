from __future__ import annotations

from dataclasses import replace

from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import MakeRectDimPart
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.Sketch import ConstraintRef


def input_value(raw, settings):
    return RectDimInput(tuple(raw["width_text_m"]), tuple(raw["height_text_m"]),
                        settings.DesignIntent, settings.SelectedLeader, raw["route_centerline"])


def malformed(document, settings, presentation):
    sketch, feature = document.sketches[0], document.feature_timeline[0]
    rules = sketch.constraints
    width = next(parameter for parameter in document.parameters if parameter.owner_id == sketch.id and parameter.name == "D1")

    def changed_parameter(**fields):
        return replace(document, parameters=tuple(replace(parameter, **fields) if parameter is width else parameter for parameter in document.parameters))

    def changed_relation(index, **fields):
        return replace(document, sketches=(replace(sketch, constraints=tuple(replace(rule, **fields) if ordinal == index else rule for ordinal, rule in enumerate(rules))),))

    def changed_feature(**fields):
        return replace(document, feature_timeline=(replace(feature, definition=replace(feature.definition, **fields)),))

    cases = (
        ("reverse_direction", changed_feature(reversed=True), presentation),
        ("mid_plane", changed_feature(symmetric=True), presentation),
        ("through_all", changed_feature(end_condition=ExtrudeEnd.KThroughAll), presentation),
        ("inactive_configuration", replace(document, configurations=(replace(document.configurations[0], active=False),)), presentation),
        ("wrong_parameter_value", changed_parameter(value=replace(width.value, value=float(width.value.value) + 1.0)), presentation),
        ("wrong_parameter_owner", changed_parameter(owner_id=feature.id), presentation),
        ("unowned_parameter_label", changed_parameter(name="D7@ForeignSketch"), presentation),
        ("missing_axis", replace(document, sketches=(replace(sketch, constraints=rules[1:]),)), presentation),
        ("duplicate_axis", replace(document, sketches=(replace(sketch, constraints=(rules[0], *rules[1:3], replace(rules[0], id=rules[3].id), *rules[4:])),)), presentation),
        ("swapped_axis", changed_relation(0, kind="vertical"), presentation),
        ("wrong_axis_point", changed_relation(0, references=(ConstraintRef(sketch.entities[0].id, "start"),)), presentation),
        ("swapped_length_owner", changed_relation(4, parameter_id=rules[5].parameter_id), presentation),
        ("reversed_distance_endpoints", changed_relation(4, references=tuple(reversed(rules[4].references))), presentation),
        ("suppressed_relation", changed_relation(0, suppressed=True), presentation),
        ("driven_relation", changed_relation(4, driving=False), presentation),
        ("extra_relation_metadata", changed_relation(0, attributes={"unprojected": True}), presentation),
        ("wrong_text_side", document, {**presentation, "width_text_m": [presentation["width_text_m"][0], 1.0]}),
        ("text_outside_span", document, {**presentation, "height_text_m": [presentation["height_text_m"][0], 1.0]}),
        ("untyped_routeflag", document, {**presentation, "route_centerline": 1}),
        ("extra_metadata", replace(document, metadata={**document.metadata, "extra": "unprojected"}), presentation),
    )
    result = []
    for name, candidate, raw in cases:
        try:
            MakeRectDimPart(candidate, settings, input_value(raw, settings))
        except (ValueError, TypeError, KeyError) as error:
            result.append({"case": name, "rejected": True, "exception": type(error).__name__, "diagnostic": str(error)})
        else:
            raise ValueError("malformed dimensioned complete neutral part was accepted: " + name)
    return result
