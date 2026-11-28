from __future__ import annotations

from math import hypot

from Core import ArchiveError
from convert.adapters.base.SafeParsing import ParseUntrusted
from ProfileTransform import stored_frame
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved


def _parameter(display):
    (handle_row,) = display["f850"]
    handle = handle_row["o"]
    dimension = handle["ff0"]
    return handle, dimension, dimension["f28"]


def _keyword_view(archive, cut):
    keywords = archive.require("swXmlContents/KeyWords")
    if keywords[0] != 0x86 or not keywords.endswith(b"\r\n"):
        raise ArchiveError("unexpected generated keyword framing")
    xml = ParseUntrusted(keywords[1:])
    row = next(element for element in xml if element.get("id") == str(cut["f08"]))
    (dimension,) = row.findall("Dimension")
    return {
        "tag": row.tag, "name": row.get("Name"), "type": row.get("Type"),
        "profile_id": int(row.attrib["DissectableChildren"]),
        "dimension": dimension.attrib["Name"], "depth_in_document_units": float(dimension.text),
    }


def _circle_view(profile):
    sketch = profile["pd_f80"]
    (arc_row,) = sketch["arcs"]
    arc = arc_row["arc"]
    one_end, other_end, center_index = (arc[key] for key in ("fc8_s", "fcc_s", "fdc_s"))
    center = sketch["points"][center_index]["point"]["pos"]
    marker = sketch["points"][one_end]["point"]["pos"]
    dimensions = sketch["dims"]
    (fixed,) = dimensions["log_g1"]
    (value,) = dimensions["val_g1"]
    (presentation,) = dimensions["f118"]["items"]
    (handle_row,) = presentation["o"]["f850"]
    radial, handle = value["d"], handle_row["o"]
    return {
        "counts": [len(sketch[name]) for name in ("points", "lines", "arcs")],
        "frame": stored_frame((profile,)),
        "center_m": [center["x"], center["y"]],
        "radius_m": hypot(marker["x"] - center["x"], marker["y"] - center["y"]),
        "closed": one_end == other_end and one_end != center_index,
        "fixed_center": fixed["d"]["f80"] == 0x11 and fixed["d"]["h1"]["idx"] == center_index,
        "radial_link": radial.cls == "sgCircleDim" and radial["f80"] == 3
        and radial["h1"]["idx"] == 0 and handle.cls == "moSkDimHandleRadial_c"
        and handle["ff0"] is sketch and handle["ff8"] == 0,
        "parameter_m": radial["f28"]["f58"],
    }


def read_blind_cut(archive, registry):
    config_name = "Contents/Config-0"
    resolved_name = config_name + "-ResolvedFeatures"
    config, config_reader = load_config(archive.require(config_name), registry, 19000, archive=archive, name=config_name)
    resolved, reader = load_resolved(
        archive.require(resolved_name), registry, 19000, archive=archive, name=resolved_name,
        seed=config_reader.map_state(),
    )
    if config.tail or resolved.tail or config_reader.left() or reader.left():
        raise ArchiveError("blind cut structural readback left unread archive bytes")
    user_roots = [node for node in resolved.roots
                  if node.cls in ("moProfileFeature_c", "moExtrusion_c", "moICE_c")]
    if [node.cls for node in user_roots] != ["moProfileFeature_c", "moExtrusion_c", "moProfileFeature_c", "moICE_c"]:
        raise ArchiveError("blind cut discovery requires the two complete ordered feature pairs")
    boss_profile, boss, cut_profile, cut = user_roots
    end = cut["f818"]
    display = end["f18"]
    handle, dimension, parameter = _parameter(display)
    boss_parameter = _parameter(boss["f818"]["f18"])[2]
    return {
        "feature_names": [node["f18"]["f08"] for node in user_roots],
        "distinct_feature_ids": len({node["f08"] for node in user_roots}) == len(user_roots),
        "profile_ids": [boss_profile["f08"], cut_profile["f08"]],
        "owned_profiles": all(
            len(node["f60"]["list"]["items"]) == 1 and node["f60"]["list"]["items"][0]["o"] is profile
            for node, profile in ((boss, boss_profile), (cut, cut_profile))
        ),
        "distinct_plane_wrappers": boss_profile["pd_f78"] is not cut_profile["pd_f78"]
        and boss_profile["pd_f78"]["f58"] is not cut_profile["pd_f78"]["f58"],
        "cut_profile": _circle_view(cut_profile),
        "end": {key: end[key] for key in ("f08", "f88", "f8c", "f0c", "f10", "f158")},
        "inactive_ends_absent": end["f20"] is end["fc8"] is end["fd0"] is None and end["f140"]["t"] == 0,
        "depth_parameter": {
            "name": parameter["f18"]["f08"], "value_m": parameter["f58"],
            "classes": [display.cls, handle.cls, dimension.cls, parameter.cls],
            "distinct_from_boss": parameter is not boss_parameter,
        },
        "operations": [node["f810"] for node in (boss, cut)],
        "cut_flags": cut["f28"],
        "scope_word": cut["f544"],
        "constructor_body_state": all(cut[key] == 0 for key in (
            "has_f528", "has_f530", "has_f548", "n494", "has_f4a8", "has_f4b0", "has_f4c0", "has_f4c8",
        )) and cut["f538"] is None and "f558" not in cut.f,
        "body_scope_qualified": False,
        "keyword": _keyword_view(archive, cut),
    }
