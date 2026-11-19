WRAPPER = "d8982a8caef31e4c62ed49b70d3747f701fee0622bbaec7a550d6e874327e959"
CAPTURE = "37ea8f73e3c278f0182cd266107fbba0bd9b31c937a99d727367ee7732936a78"
METADATA = "8976ff4c41ed2fd4be04102f4d0fbcb39a0458f743e909ba8eaee741a0a9fd3b"
MEMBERS = {
    "IEdge": "GetBody",
    "IPartDoc": "GetBodies2",
    "IBody2": "GetEdges",
    "IEntity": "GetComponent",
    "ISldWorks": "IsSame",
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def validate(metadata):
    require(
        metadata["wrapper_sha256"] == WRAPPER
        and metadata["tool_sha256"] == CAPTURE
        and metadata["cad_objects_created"]
        == metadata["native_processes_started_by_tool"]
        == metadata["model_documents_opened"]
        == 0,
        "exact zero-CAD body API capture is required",
    )
    require(
        all(
            (row["major"], row["minor"]) == (34, 0)
            for row in metadata["libraries"].values()
        ),
        "body API library release differs",
    )
    expected = {
        "IEdge": ("{83A33D42-27C5-11CE-BFD4-00400513BB57}", 37, 344),
        "IPartDoc": ("{83A33D32-27C5-11CE-BFD4-00400513BB57}", 132, 1136),
        "IBody2": ("{3A075BFD-9962-4431-8321-7AF4903C55AD}", 125, 1064),
        "IEntity": ("{83A33D65-27C5-11CE-BFD4-00400513BB57}", 65545, 120),
        "ISldWorks": ("{83A33D22-27C5-11CE-BFD4-00400513BB57}", 283, 2416),
    }
    rows = {}
    for name, member in MEMBERS.items():
        interface = metadata["interfaces"][name]
        require(interface["missing"] == [], "body API interface is incomplete")
        selected = [
            row
            for row in interface["members"]
            if row["names"][0] == member and row["invoke_kind"] == 1
        ]
        require(len(selected) == 1, "body API method shape is ambiguous")
        row = selected[0]
        require(
            interface["guid"] == expected[name][0]
            and row["member_id"] == expected[name][1]
            and row["vtable_offset_bytes"] == expected[name][2]
            and row["function_ordinal"] * 8 == row["vtable_offset_bytes"],
            "exact body API identity or vtable slot differs",
        )
        rows[name] = row
    for name in ("IEdge", "IBody2", "IEntity"):
        require(rows[name]["arguments"] == [], "body API zero-argument method differs")
    require(
        rows["IEdge"]["return_type"] == [[26, [29, 50332672]], 0, None],
        "actual typed body return differs",
    )
    require(
        rows["IPartDoc"]["arguments"] == [[3, 1, None], [11, 1, None]]
        and rows["IPartDoc"]["return_type"] == [12, 0, None]
        and rows["IBody2"]["return_type"] == [12, 0, None],
        "part/body inventory signatures differ",
    )
    require(
        rows["IEntity"]["member_id"] == 65545
        and rows["IEntity"]["return_type"] == [9, 0, None]
        and rows["ISldWorks"]["member_id"] == 283
        and rows["ISldWorks"]["arguments"] == [[9, 1, None], [9, 1, None]]
        and rows["ISldWorks"]["return_type"] == [3, 0, None],
        "existing entity/equality signatures differ",
    )
    require(
        metadata["enums"]["swBodyType_e"]["swSolidBody"] == 0
        and metadata["enums"]["swObjectEquality"]["swObjectSame"] == 1,
        "body/equality enum values differ",
    )
    return rows


def prove_owner(author, child, component, edge, expected, edge_points, endpoints_match):
    metadata = author.edge_body_metadata
    validate(metadata)
    part = author.typed(child, "IPartDoc")
    bodies = list(author.get(part, "GetBodies2", 0, False) or ())
    repeated = list(author.get(part, "GetBodies2", 0, False) or ())
    require(
        len(bodies) == len(repeated) == 1,
        "actual resolved part must retain one live solid body",
    )
    body = author.typed(bodies[0], "IBody2")
    repeated_body = author.typed(repeated[0], "IBody2")
    native_edge = author.typed(edge, "IEdge")
    raw_owner = author.get(native_edge, "GetBody")
    require(raw_owner is not None, "selected edge has no actual native body")
    owner = author.typed(raw_owner, "IBody2")
    codes = {
        "part_body_self": author.get(author.app, "IsSame", body, body),
        "part_body_repeated": author.get(author.app, "IsSame", body, repeated_body),
        "edge_body_self": author.get(author.app, "IsSame", owner, owner),
        "edge_self": author.get(author.app, "IsSame", native_edge, native_edge),
        "edge_body_vs_actual_part_body": author.get(author.app, "IsSame", owner, body),
    }
    result = {
        "rule": "sole-resolved-part-body-and-exact-live-edge-membership-v1",
        "actual_part_body_count": len(bodies),
        "equality_codes": codes,
        "body_edges": [],
        "proved": False,
    }
    author.rec.data.setdefault("edge_body_observations", []).append(result)
    author.rec.flush()
    require(
        all(type(value) is int and value == 1 for value in codes.values()),
        "selected edge body differs from actual resolved part body or equality control",
    )
    raw_edges = list(author.get(body, "GetEdges") or ())
    require(
        len(raw_edges) == 12,
        "ordinary rectangular prism must have twelve actual body edges",
    )
    matched = []
    for index, raw in enumerate(raw_edges):
        actual, points = edge_points(author, raw)
        equality = author.get(author.app, "IsSame", actual, native_edge)
        require(
            type(equality) is int and equality in (0, 1),
            "body-edge equality is unsupported or invalid",
        )
        result["body_edges"].append(
            {"index": index, "endpoints_m": points, "selected_edge_equality": equality}
        )
        if equality == 1:
            require(
                endpoints_match(points, expected),
                "live matching body edge has different analytic endpoints",
            )
            matched.append(index)
    author.rec.flush()
    require(
        len(matched) == 1,
        "selected edge must match exactly one actual edge of the live part body",
    )
    raw_component = author.get(author.typed(edge, "Entity"), "GetComponent")
    result["contextual_component_null"] = raw_component is None
    if raw_component is not None:
        result["contextual_component_equality"] = author.get(
            author.app, "IsSame", raw_component, component
        )
        require(
            result["contextual_component_equality"] == 1,
            "non-null contextual component differs from actual visible component",
        )
    result["matched_body_edge_index"] = matched[0]
    result["proved"] = True
    author.rec.flush()
    return result
