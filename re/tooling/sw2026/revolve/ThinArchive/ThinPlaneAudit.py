from collections import deque
from math import copysign
from struct import unpack

from AuditRevEndOwners import ArchiveNode, NativeRows, ReadNativeLink, SldprtArchive, audit_streams, digest, observe_ends, require
from BuildThinControls import expected
from RevolveFamilyModel import world
from RevolveStreamAudit02 import stream_audit
from ThinNeutral import MODES
from ThinWireOwners import check_open_profile, check_walls, require_positions

from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseXml


def point_fields(value):
    return tuple(value[key] for key in "xyz")


def verify_frame(case, dimension, span):
    start, stop, axial = span
    a, b = (world(case, (value, axial, 0.0)) for value in (start, stop))
    sense = copysign(1.0, stop - start)
    u, v, w = (world(case, point) for point in ((sense, 0, 0), (0, 0, sense), (0, -1, 0)))
    compare_points(dimension, ("f80", "fa0"), (a, b))
    compare_points(dimension, ("fe0", "fe8"), (u, v))
    frame = dimension["ff0"]
    matrix = [value for row in zip(u, v, w, strict=True) for value in row]
    inverse_shift = tuple(-sum(x * y for x, y in zip(a, basis, strict=True)) for basis in (u, v, w))
    require(frame["has_matrix"] == 1 and frame["f70"] == 1.0 and frame["f78"] == 0,
            "thin wall requires the actual inverse frame")
    require_positions([frame["f08"][f"m{i}"] for i in range(9)], matrix, "thin wall inverse matrix differs")
    require_positions([frame[key] for key in ("f58", "f60", "f68")], inverse_shift, "thin wall inverse shift differs")
    return {"points_m": [point_fields(dimension[key]) for key in ("f80", "fa0")],
            "radial": point_fields(dimension["fe0"]), "normal": point_fields(dimension["fe8"]),
            "inverse_matrix": matrix, "inverse_shift_m": inverse_shift}


def compare_points(dimension, names, points):
    for name, point in zip(names, points, strict=True):
        require_positions(point_fields(dimension[name]), point, "typed dimension placement differs from supported frame")


def measure_plane(raw, case, ground_truth=None):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    (feature,) = [node for node in link.ResolvedValue.RootsValue if isinstance(node, ArchiveNode)
                  and node.ClassValue.NameValue == "moRevolutionThin_c"]
    fields = feature.FieldsValue
    mode = MODES[case["wall_mode"]]
    thin = fields["f8f0"]
    require(fields["f824"] == 0 and fields["f828"] == 5 and thin.FieldsValue["f28"] == mode,
            "principal thin feature direction or mode differs")
    truth = expected(case) if ground_truth is None else ground_truth
    if ground_truth is None:
        truth["profile"]["frame_points"] = [list(world(case, row)) for row in truth["profile"]["frame_points"]]
    profile = check_open_profile(link, feature, truth["definition"], truth["profile"])
    angles = observe_ends(link, feature)
    require(angles["angles"]["f20"] is None and angles["angles"]["f18"]["name"] == "D1",
            "principal thin angle lost its exact D1 owner")
    require_positions((angles["angles"]["f18"]["radians"],), (truth["drivers"]["angle"]["value"],),
                      "principal thin angle differs from actual authored intent")
    axis = fields["f830"].FieldsValue
    compare_points(axis, ("fc8", "fe0"),
                     (world(case, (case["axis_x_m"], case["axis_axial_m"][0], 0)),
                      world(case, (0, 1, 0))))
    spans = deque()

    def note_span(_row, start, stop, axial):
        spans.append((start, stop, axial))

    walls = check_walls(thin, mode, truth, profile, link, place=note_span)
    placements = {}
    for slot in ("f08", "f10"):
        display = thin.FieldsValue[slot]
        (item,) = NativeRows(display.FieldsValue["f850"])
        dimension = item["o"].FieldsValue["ff0"].FieldsValue
        if slot in walls["active"]:
            placements[slot] = verify_frame(case, dimension, spans.popleft())
        else:
            require(all(point_fields(dimension[key]) == (0.0, 0.0, 0.0) for key in ("f80", "fa0"))
                    and not dimension["has_fe0"] and not dimension["has_ff0"], "inactive wall gained spatial state")
        if ground_truth is None:
            stored, = unpack("<d", display.FieldsValue["f5b0"]["data"])
            require(stored == walls[slot]["metres"], "thin display cache lost its live independent value")
    require(not spans, "typed walls lost their authored spans")
    if ground_truth is None:
        require(not fields["has_f528"] and thin.FieldsValue["f48"] is None and thin.FieldsValue["f30"] == -2.0,
                "archived cold candidate carries an unqualified cache or end thickness")
        streams, history = stream_audit(archive, link)
        streams |= history
        require(len(streams) == 10 and all(row["byte_identity"] for row in streams.values()),
                "principal thin generated archive did not replay exactly")
        keywords = ParseXml(archive.require(KeywordsStream))
        (row,) = [row for row in keywords if row.attrib.get("Type") == "Revolve-Thin"]
        names = [tag.attrib["Name"] for tag in row if tag.tag == "Dimension"]
        require(names == (["D1", "D4", "D3"] if mode == 3 else ["D3", "D1"]),
                "principal thin keywords lost actual driver order")
    else:
        streams = audit_streams(archive, link)
    return {"sha256": digest(raw), "bytes": len(raw), "mode": mode, "placements": placements,
            "profile_frame": profile["frame"], "axis_world": {key: point_fields(axis[key]) for key in ("fc8", "fe0")},
            "typed_streams": streams}
