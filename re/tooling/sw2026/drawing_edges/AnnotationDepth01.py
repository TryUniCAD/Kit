from math import isclose, isfinite

METADATA = "195f6c97fdb1f233897714040c9c664e6c58afefd934e30b4991e55e5b9134cc"
CAPTURE = "bfd276fcbcdef7e2c48998695ee17207373e5831cf8e06de69a3b12fe47f2d71"
WRAPPER = "d8982a8caef31e4c62ed49b70d3747f701fee0622bbaec7a550d6e874327e959"
RULE = "constant-attached-cap-depth-under-actual-front-view-transform-v1"


def require(value, message):
    if not value:
        raise RuntimeError(message)


def validate(metadata):
    require(
        metadata["tool_sha256"] == CAPTURE
        and metadata["wrapper_sha256"] == WRAPPER
        and metadata["cad_objects_created"]
        == metadata["native_processes_started_by_tool"]
        == metadata["model_documents_opened"]
        == 0,
        "exact zero-CAD annotation depth API metadata is required",
    )
    expected = {
        "IAnnotation": {
            ("GetPosition", 1): (8, 112, [], [12, 0, None]),
            ("SetPosition2", 1): (91, 904, [[5, 1, None]] * 3, [11, 0, None]),
            ("GetPlane", 1): (92, 912, [], [12, 0, None]),
        },
        "IMathTransform": {("ArrayData", 2): (3, 72, [], [12, 0, None])},
        "IView": {
            ("ModelToViewTransform", 2): (
                221,
                1896,
                [],
                [[26, [29, 50334080]], 0, None],
            )
        },
    }
    for name, members in expected.items():
        interface = metadata["interfaces"][name]
        require(interface["missing"] == [], "annotation depth interface is incomplete")
        for (member, kind), values in members.items():
            rows = [
                row
                for row in interface["members"]
                if row["names"][0] == member and row["invoke_kind"] == kind
            ]
            require(len(rows) == 1, "annotation depth API member is ambiguous")
            row = rows[0]
            require(
                (
                    row["member_id"],
                    row["vtable_offset_bytes"],
                    row["arguments"],
                    row["return_type"],
                )
                == values,
                "annotation depth API shape differs",
            )
    return True


def plan(case):
    matrix = case["expected"]["view"]["model_to_view"]
    require(
        len(matrix) == 16
        and all(type(x) in (int, float) and isfinite(x) for x in matrix),
        "invalid explicit model-to-view transform",
    )
    require(
        case["expected"]["view"]["orientation"] == "*Front"
        and matrix[:9] == [1, 0, 0, 0, 1, 0, 0, 0, 1]
        and matrix[12] == 1,
        "note depth probe admits only the existing canonical Front unit-scale profile",
    )
    endpoints = case["edge_endpoints_m"]
    require(
        len(endpoints) == 2
        and all(
            len(point) == 3 and point[2] == case["prism_m"]["maximum"][2]
            for point in endpoints
        ),
        "note must attach to the existing far-cap rail",
    )
    projected = [point[2] * matrix[12] + matrix[11] for point in endpoints]
    require(
        projected[0] == projected[1], "attachment edge has nonconstant projected depth"
    )
    require(
        all(
            case["annotation"][name][2] == 0
            for name in ("before_position_m", "after_position_m")
        ),
        "preserve the original authored sheet-plane requests",
    )
    depth = case["prism_m"]["maximum"][2] - case["prism_m"]["minimum"][2]
    return {
        "rule": RULE,
        "model_edge_endpoints_m": endpoints,
        "model_to_view": matrix,
        "projected_endpoint_z_m": projected,
        "expected_note_z_m": projected[0],
        "independent_requested_z_probes_m": [depth / 3, -2 * depth / 7],
        "native_planar_setter_bound": True,
        "attachment_to_view_frame_rule_qualified": False,
        "scope": "frozen source-bound hypothesis; native control and independent generated depth still required",
    }


def context(author, view, edge, case, edge_points):
    validate(author.annotation_depth_metadata)
    result = plan(case)
    transform = author.typed(author.get(view, "ModelToViewTransform"), "IMathTransform")
    actual = list(author.get(transform, "ArrayData"))
    require(len(actual) == 16, "actual view transform has the wrong size")
    for index, (observed, expected) in enumerate(
        zip(actual, result["model_to_view"], strict=True)
    ):
        author.rec.close_number(
            "annotation actual view transform " + str(index),
            observed,
            expected,
            absolute=2e-9,
        )
    _, points = edge_points(author, edge)
    observed_depths = [point[2] * actual[12] + actual[11] for point in points]
    require(
        all(
            isclose(value, result["expected_note_z_m"], rel_tol=2e-7, abs_tol=2e-9)
            for value in observed_depths
        ),
        "actual picked edge has a different projected cap depth",
    )
    result["actual_model_to_view"] = actual
    result["actual_projected_endpoint_z_m"] = observed_depths
    return result


def expected_position(requested, depth):
    require(
        len(requested) == 3 and depth["rule"] == RULE,
        "annotation depth prediction is unavailable",
    )
    return [requested[0], requested[1], depth["expected_note_z_m"]]
