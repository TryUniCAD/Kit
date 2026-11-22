from math import hypot

from convert import open_document
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.CirclePointIndex import FindCirclePoint
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import ReadPrismParam
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def alter_radius(profile, boss, *, saved):
    sketch = profile.FieldsValue["pd_f80"].FieldsValue
    arc = sketch["arcs"][0]["arc"]
    center = sketch["points"][FindCirclePoint(arc, "fdc")]["point"]["pos"]
    seam = sketch["points"][FindCirclePoint(arc, "fc8")]["point"]["pos"]
    parameter = sketch["dims"]["val_g1"][0]["d"].FieldsValue["f28"].FieldsValue
    original = parameter["f58"]
    for name in ("x", "y"):
        seam[name] = center[name] + 1.125 * (seam[name] - center[name])
    parameter["f58"] = original * 1.125
    if saved:
        _, _, inactive = ReadPrismParam(boss.FieldsValue["f818"].FieldsValue["f20"], False)
        diameter = 2 * parameter["f58"]
        diagonal = hypot(diameter, diameter, inactive)
        for slot in ("f4a8", "f4c0"):
            chooser = boss.FieldsValue[slot]["f48"]["items"][0]["o"].FieldsValue
            chooser["f48"]["items"][0]["o"].FieldsValue["f28"] = diagonal
    return [original.hex(), parameter["f58"].hex()]


def alter_depth(owner, *, saved):
    parameter = owner.DepthValue.Parameter.FieldsValue
    original = parameter["f58"]
    parameter["f58"] = original + 0.001125
    if not saved:
        _, inactive, _ = ReadPrismParam(owner.EndValue.FieldsValue["f20"], False)
        inactive.FieldsValue["f58"] = parameter["f58"]
    return [original.hex(), parameter["f58"].hex()]


def encode_contrast(archive, model, kind):
    link = ReadNativeLink(archive, 0)
    index = IndexFeatures(link)
    profile = index[model.sketches[0].object_id]
    boss = index[model.operations[0].object_id]
    saved = profile.FieldsValue["f3c0"] == 1
    if kind == "radius":
        words = alter_radius(profile, boss, saved=saved)
    else:
        words = alter_depth(ReadExtrude(link, boss, index), saved=saved)
    config = link.ConfigValue
    resolved = link.ResolvedValue
    config_bytes, graph = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    resolved_bytes, _ = WriteResolMut(resolved.RootsValue, resolved.ExtraFields,
                                      19000, graph.MapValue, resolved.ContextValue)
    streams = dict(archive.streams) | {link.ConfigName: config_bytes, link.StreamName: resolved_bytes}
    payload = BuildSldprt(streams, FormatVersion=archive.format_version)
    decoded = SldprtArchive.from_bytes(payload)
    changed = {name for name in archive.streams if decoded.require(name) != archive.require(name)}
    if not changed or changed - {link.ConfigName, link.StreamName}:
        raise ValueError("dimension contrast changed an owner outside the typed model")
    if decoded.require(KPartitionStream) != archive.require(KPartitionStream):
        raise ValueError("dimension contrast changed the active physical and rollback carrier")
    return payload, words


def check_dimension_conflicts(archive, model):
    results = {}
    for kind, expected in (("radius", "active cylinder radius differs from the owned sketch"),
                           ("depth", "active cap planes disagree with the boss extent")):
        payload, words = encode_contrast(archive, model, kind)
        failures = {}
        for by_name, include_brep in (("geometry", True), ("design", False)):
            options = {"source_format": "solidworks.sldprt", "include_brep": include_brep,
                       "include_tessellation": False}
            try:
                open_document(payload, strict=True, **options)
            except SldprtFormatError as error:
                failures[by_name] = str(error)
            else:
                raise ValueError(f"strict {by_name} accepted conflicting {kind}")
            if expected not in failures[by_name]:
                raise ValueError(f"{kind} stopped before independent physical proof: {failures[by_name]}")
        results[kind] = {"typed_driver_metres_hex": words, "strict": failures}
    return results
