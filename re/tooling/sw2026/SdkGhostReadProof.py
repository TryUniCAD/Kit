from hashlib import sha256
from pathlib import Path
from sys import argv, path
import json


if len(argv) < 3:
    raise ValueError("expected an SDK checkout and at least one disclosed native input")
root = Path(argv[1]).resolve()
path[:0] = [str(root / "src"), str(root)]

from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def read_sample(file):
    data = file.read_bytes()
    archive = SldprtArchive.from_bytes(data)
    link = ReadNativeLink(archive, 0)
    cfg, resolved = link.ConfigValue, link.ResolvedValue
    configuration, rebuilt = WriteConfigMut(cfg.RootValue, 19000, cfg.HeaderValue)
    emitted, repeated = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000,
                                      rebuilt.MapValue, resolved.ContextValue)
    if (configuration != archive.require(link.ConfigName) or emitted != archive.require(link.StreamName)
            or cfg.MapValue != rebuilt.MapValue or resolved.MapValue != repeated.MapValue
            or not cfg.ReportValue["completed"] or not resolved.ReportValue["completed"]):
        raise ValueError("complete linked stream or map changed for " + file.name)
    manager = cfg.RootValue.FieldsValue["fd90"]
    objects = []
    for node in manager["objects"]:
        value = node["o"]
        objects.append({"identifier_count": value["nb0"], "point_count": value["nf0"],
                        "object_present_flag": value["has_f50"],
                        "conditional_object_is_null": value.get("f50") is None})
    if manager["n"] != len(objects) or not objects:
        raise ValueError("source requires a populated actual ghost body manager")
    return {"file": file.name, "source_sha256": sha256(data).hexdigest(), "ghost_objects": objects,
            "config_sha256": sha256(configuration).hexdigest(), "resolved_sha256": sha256(emitted).hexdigest(),
            "config_map_counter": cfg.MapValue.CounterValue, "resolved_map_counter": resolved.MapValue.CounterValue,
            "sdk_config_exact": True, "sdk_resolved_exact": True}


print(json.dumps({"passed": True, "files": [read_sample(Path(value)) for value in argv[2:]]}, sort_keys=True))
