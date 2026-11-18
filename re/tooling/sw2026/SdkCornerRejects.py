from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from SdkBlindPartChecks import require
from SdkRectDimRejects import input_value
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import PlaneFrame
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import MakeCornerMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut


def fresh(document, inputs, presentation):
    plan = ProjectRectDims(document)
    allocator = PersistentIds()
    system = MakePartBaseMut(inputs, plan, allocator)
    profile = MakePartProfMut(system, inputs, plan, allocator)
    MakeRectDimsMut(profile, input_value(presentation, inputs), allocator)
    return profile, system.OriginValue


def snapshot(profile, origin):
    sketch = profile.GeometryValue.SketchValue
    fields = sketch.FieldsValue
    return (deepcopy(fields["f140"]), fields["npoints"], fields["dims"]["nlog2"],
            tuple(id(row) for row in fields["points"]), tuple(id(row) for row in fields["dims"]["log_g2"]),
            tuple(point.FieldsValue["f20"] for point in profile.GeometryValue.PointValues),
            origin.PointValue.FieldsValue["f08"])


def malformed(document, inputs, presentation):
    outcomes = []
    for label in ("off_origin_frame", "wrong_origin_owner", "nonempty_origin_creation_log", "moved_origin_point",
                  "missing_value_driver", "existing_coincidence", "wrong_point_handle_slot", "wrong_line_endpoint_slot",
                  "foreign_local_point", "wrong_next_creation_id", "nonrectangular_contour", "wrong_axis_relation",
                  "stale_constraint_count", "already_anchored"):
        profile, origin = fresh(document, inputs, presentation)
        sketch = profile.GeometryValue.SketchValue
        if label == "off_origin_frame":
            profile = replace(profile, FrameValue=PlaneFrame((1.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                                                           (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
        elif label == "wrong_origin_owner":
            origin.ProfileValue.FieldsValue["owner"] = None
        elif label == "nonempty_origin_creation_log":
            origin.ProfileValue.FieldsValue["f3dc"] = 1
        elif label == "moved_origin_point":
            origin.PointValue.FieldsValue["pos"]["x"] = 1.0
        elif label == "missing_value_driver":
            sketch.FieldsValue["dims"]["val_g2"] = ()
        elif label == "existing_coincidence":
            sketch.FieldsValue["dims"]["nlog2"] = 1
            sketch.FieldsValue["dims"]["log_g2"] = ({"d": {}},)
        elif label == "wrong_point_handle_slot":
            sketch.FieldsValue["dims"]["val_g2"][0]["d"].FieldsValue["h1"].FieldsValue["idx"] = 3
        elif label == "wrong_line_endpoint_slot":
            profile.GeometryValue.LineValues[0].FieldsValue["fc8_s"] = 3
        elif label == "foreign_local_point":
            profile.GeometryValue.PointValues[0].FieldsValue["_sketch"] = origin.SketchValue
        elif label == "wrong_next_creation_id":
            sketch.FieldsValue["f140"]["f08"] = 7
        elif label == "nonrectangular_contour":
            profile.GeometryValue.PointValues[2].FieldsValue["pos"]["x"] += 0.001
        elif label == "wrong_axis_relation":
            sketch.FieldsValue["dims"]["log_g1"][0]["d"]["f80"] = 5
        elif label == "stale_constraint_count":
            profile.GeometryValue.PointValues[0].FieldsValue["f20"] = 7
        elif label == "already_anchored":
            MakeCornerMut(profile, origin)
        before = snapshot(profile, origin)
        try:
            MakeCornerMut(profile, origin)
        except (ValueError, TypeError) as error:
            require(snapshot(profile, origin) == before, "rejected anchor partially published graph mutations: " + label)
            outcomes.append({"case": label, "rejected": True, "publication_unchanged": True,
                             "exception": type(error).__name__, "diagnostic": str(error)})
        else:
            raise ValueError("unsupported anchor accepted: " + label)
    return outcomes
