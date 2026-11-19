WRAPPER = "d8982a8caef31e4c62ed49b70d3747f701fee0622bbaec7a550d6e874327e959"
CAPTURE = "4cfde281387575e4cfefb825a4a391f589a6944e11984d584427159ab8254afa"
METADATA = "3c02263dc1d85eb15c1446537b4aa8376cdddde715544f7cf6ef662c3ac79b81"
RULE = "native-part-correspondence-and-exact-live-edge-membership-v1"


def require(value, message):
    if not value:
        raise RuntimeError(message)


def validate(metadata):
    require(
        metadata["wrapper_sha256"] == WRAPPER
        and metadata["tool_sha256"] == CAPTURE
        and metadata["cad_objects_created"]
        == metadata["model_documents_opened"]
        == metadata["native_processes_started_by_tool"]
        == 0,
        "exact zero-CAD correspondence metadata is required",
    )
    require(
        all(
            (row["major"], row["minor"]) == (34, 0)
            for row in metadata["libraries"].values()
        ),
        "correspondence API library differs",
    )
    expected = {
        "IView": (
            "{83A33D50-27C5-11CE-BFD4-00400513BB57}",
            {"GetCorresponding": (445, 3816), "GetCorrespondingEntity": (446, 3824)},
        ),
        "IModelDocExtension": (
            "{99F4D4AF-F268-4EE1-8C55-041F7BECF879}",
            {"GetCorresponding2": (303, 2600), "GetCorrespondingEntity2": (304, 2608)},
        ),
    }
    for interface, (guid, members) in expected.items():
        observed = metadata["interfaces"][interface]
        require(
            observed["guid"] == guid and observed["missing"] == [],
            "correspondence interface identity or coverage differs",
        )
        for name, (dispid, slot) in members.items():
            rows = [
                row
                for row in observed["members"]
                if row["names"][0] == name and row["invoke_kind"] == 1
            ]
            require(len(rows) == 1, "correspondence method is ambiguous")
            row = rows[0]
            require(
                row["member_id"] == dispid
                and row["vtable_offset_bytes"] == slot
                and row["function_ordinal"] * 8 == slot
                and row["arguments"] == [[9, 1, None]]
                and row["return_type"] == [9, 0, None],
                "correspondence method shape differs",
            )
    return expected


def map_to_part(author, view, child, edge, expected, edge_points, endpoints_match):
    validate(author.edge_correspondence_metadata)
    extension = author.typed(author.get(child, "Extension"), "IModelDocExtension")
    raw = author.get(extension, "GetCorrespondingEntity2", edge)
    require(raw is not None, "actual underlying part did not map the drawing edge")
    mapped, points = edge_points(author, raw)
    require(
        endpoints_match(points, expected),
        "mapped part edge has different analytic endpoints",
    )
    repeated = author.get(extension, "GetCorrespondingEntity2", edge)
    require(repeated is not None, "repeated drawing-to-part correspondence is null")
    repeated = author.typed(repeated, "IEdge")
    forward_raw = author.get(view, "GetCorrespondingEntity", mapped)
    require(forward_raw is not None, "actual drawing view did not map its part edge")
    forward, forward_points = edge_points(author, forward_raw)
    require(
        endpoints_match(forward_points, expected),
        "forward corresponding edge has different analytic endpoints",
    )
    roundtrip = author.get(extension, "GetCorrespondingEntity2", forward)
    require(roundtrip is not None, "native edge correspondence round trip is null")
    roundtrip = author.typed(roundtrip, "IEdge")
    codes = {
        "mapped_part_edge_self": author.get(author.app, "IsSame", mapped, mapped),
        "mapped_part_edge_repeated": author.get(author.app, "IsSame", mapped, repeated),
        "forward_drawing_edge_self": author.get(author.app, "IsSame", forward, forward),
        "forward_vs_original_drawing_edge": author.get(
            author.app, "IsSame", forward, edge
        ),
        "roundtrip_vs_mapped_part_edge": author.get(
            author.app, "IsSame", roundtrip, mapped
        ),
    }
    result = {
        "reverse_owner": "actual_referenced_part.Extension",
        "reverse_method": "GetCorrespondingEntity2",
        "forward_owner": "actual_model_view",
        "forward_method": "GetCorrespondingEntity",
        "mapped_part_endpoints_m": points,
        "forward_drawing_endpoints_m": forward_points,
        "equality_codes_within_each_domain": codes,
        "proved": False,
    }
    author.rec.data.setdefault("edge_correspondence_observations", []).append(result)
    author.rec.flush()
    require(
        all(type(value) is int and value == 1 for value in codes.values()),
        "native corresponding edge identity failed within its domain",
    )
    result["proved"] = True
    author.rec.flush()
    return mapped, result
