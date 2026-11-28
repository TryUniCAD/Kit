from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys


ORIGIN_PROOF = "kit.sw2026.material-origin-archive-proof.v1"


def require(value, message):
    if not value:
        raise ValueError(message)


def check_graph(link, family, archive):
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

    model = RequireNative(link.ConfigValue.RootValue, "moPart_c")
    roots = link.ResolvedValue.RootsValue
    profile, = [root for root in roots if root.ClassValue.NameValue == "moProfileFeature_c"]
    origin, = [root for root in roots if root.ClassValue.NameValue == "moOriginProfileFeature_c"]
    require(ReadNativeName(profile) == "AnchorSketch" and ReadNativeName(origin) == "Origin",
            "archive origin proof has the wrong actual feature names")
    stored = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch").FieldsValue
    origin_sketch = RequireNative(origin.FieldsValue["pd_f80"], "sgSketch").FieldsValue
    points, lines, relations = stored["points"], stored["lines"], stored["dims"]["log_g2"]
    expected = (5, 4, 1, 0) if family == "corner" else (6, 6, 3, 4)
    require((len(points), len(lines), len(relations)) == expected[:3]
            and stored["dims"]["ng2"] == 2 and stored["dims"]["nlog1"] == 4,
            "archive anchor changed its contour or driver topology")
    external = points[-1]["point"]
    local = points[expected[3]]["point"]
    origin_entry, = origin_sketch["points"]
    origin_point = origin_entry["point"]
    zero = {"x": 0.0, "y": 0.0}
    require(points[-1]["kind"] == 1 and points[expected[3]]["kind"] == origin_entry["kind"] == 0
            and external["fe4"] == 6 and external is not local and local is not origin_point
            and external["pos"] == local["pos"] == origin_point["pos"] == zero,
            "archive origin wrapper must retain distinct zero-position dependent points")
    entity = RequireNative(external["ext"], "sgExtEnt_c")
    wrapper = RequireNative(entity.FieldsValue["f08"], "moSketchExtRef_w")
    select = RequireNative(wrapper.FieldsValue["f58"], "moCompSketchEntHandle_c")
    component = RequireNative(select.FieldsValue["f58"], "moUnitComponent_c")
    handle = RequireNative(select.FieldsValue["f0f8"], "sgPointHandle")
    marker = origin_point["f08"]
    require(component.FieldsValue["owner"] is model
            and select.FieldsValue["ff0"]["f00"] == origin.FieldsValue["f08"]
            and select.FieldsValue["f100"] == marker == origin_point["f0c"] and marker > 0
            and handle.FieldsValue["idx"] == 0 and "f18" not in handle.FieldsValue
            and entity.FieldsValue["f28"] == "Point1@Origin",
            "typed reference chain does not bind the same model origin and actual stored point")
    mapped = {entry.IndexValue: entry.EntryValue for entry in link.ResolvedValue.MapValue.EntriesValue}
    require(all(mapped.get(node.IndexValue) is node for node in (model, profile, origin, entity, wrapper, select, component, handle)),
            "typed origin proof lost an actual mapped reference owner")
    final = relations[-1]["d"]
    require(final["f80"] == 9 and final["h1"].FieldsValue["idx"] == len(points) - 1
            and final["h2"].FieldsValue["idx"] == expected[3], "archive coincidence loses its actual proxy or local slot")
    if family == "center":
        require(local["fe4"] == 1, "center relation does not select its actual local center")
        for index, row in enumerate(relations[:-1]):
            line = lines[4 + index]["line"]
            require(line["f54"] & 8 and line["fc8_s"] == index and line["fcc_s"] == 2 + index
                    and row["d"]["f80"] == 9 and row["d"]["h1"].FieldsValue["idx"] == 4
                    and row["d"]["h2"].FieldsValue["idx"] == 4 + index,
                    "typed center does not own the two actual opposite-corner diagonals")
    return {"schema": ORIGIN_PROOF, "family": family, "origin_feature_id": origin.FieldsValue["f08"],
            "origin_point_mark": marker, "part_configuration": 0,
            "typed_origin_chain": True, "points": len(points), "lines": len(lines), "coincidences": len(relations),
            "configuration_sha256": sha256(archive.Require(link.ConfigName)).hexdigest(),
            "resolved_features_sha256": sha256(archive.Require(link.StreamName)).hexdigest()}


def main():
    root, family = sys.argv[1:]
    require(family in ("corner", "center"), "unknown anchor proof family")
    sys.path.insert(0, str(Path(root) / "src"))
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

    for name in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(name)
    raw = sys.stdin.buffer.read()
    blocked = []

    def audit(event, _):
        if event in ("open", "os.listdir", "os.scandir", "ctypes.dlopen", "os.system", "os.exec",
                     "os.fork", "os.posix_spawn") or event.startswith(("socket.", "subprocess.")):
            blocked.append(event)
            raise RuntimeError("typed origin replay attempted external input")

    sys.addaudithook(audit)
    archive = SldprtArchive.FromBytes(raw)
    outcome = check_graph(ReadNativeLink(archive, 0), family, archive)
    require(not blocked, "typed origin replay used external input")
    print(json.dumps({**outcome, "artifact_sha256": sha256(raw).hexdigest(), "denied_reads": 0},
                     sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
