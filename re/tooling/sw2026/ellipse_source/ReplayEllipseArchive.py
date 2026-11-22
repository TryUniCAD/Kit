from EllipseArchiveCustody import digest
from EllipseModel import require
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut


def exact_map(original, rewritten):
    require(original.CounterValue == rewritten.CounterValue
            and all(before.IndexValue == after.IndexValue and before.EntryValue is after.EntryValue
                    for before, after in zip(original.EntriesValue, rewritten.EntriesValue, strict=True)),
            "typed ellipse replay changed an archive class or object identity")


def replay(archive, link, *, ellipse=True):
    config, resolved = link.ConfigValue, link.ResolvedValue
    config_data, new_config = WriteConfigMut(config.RootValue, config.VersionValue, config.HeaderValue)
    resolved_data, new_resolved = WriteResolMut(
        resolved.RootsValue, resolved.ExtraFields, resolved.VersionValue,
        new_config.MapValue, resolved.ContextValue, ReplayEllipses=ellipse,
    )
    result = {}
    for name, original, data, rewritten in (
        (link.ConfigName, config, config_data, new_config),
        (link.StreamName, resolved, resolved_data, new_resolved),
    ):
        require(data == archive.require(name) and rewritten.ReportValue["completed"]
                and not rewritten.ReportValue["missing_schemas"],
                f"typed ellipse replay differs in {name}")
        exact_map(original.MapValue, rewritten.MapValue)
        result[name] = {"exact": True, "sha256": digest(data),
                        "identical_map_entries": len(original.MapValue.EntriesValue),
                        "byte_field_owners": [{key: field[key] for key in ("schema", "field", "object_class")}
                                              for field in rewritten.ReportValue["native_byte_fields"]]}
    return result
