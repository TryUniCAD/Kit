from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from json import dumps
from sys import addaudithook

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from downstream.Body import COLLECTIONS, ROOT
from downstream.CacheInputs import finalized_part_prefix
from downstream.CheckSurfaceIdentities import generated_attachment
from downstream.Components import read_component_body, write_component_body
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches
from downstream.SurfaceIdentities import clone_collected_surface, cylinder_surface_identities
from para.concentric.CylinderFace import make_feature_file


def surface_owner(representation):
    return representation.FieldsValue["f10"]["f10"].FieldsValue["f08"]


def main():
    cli = ArgumentParser()
    cli.add_argument("variant", type=int, choices=(1, 2))
    args = cli.parse_args()
    for encoding in ("latin-1", "cp1252", "utf-8", "utf-16le", "utf-16be"):
        lookup(encoding)
    attachment, _ = generated_attachment(args.variant)
    part = attachment.candidate
    config = part.CurrentConfig.FieldsValue["f08"]
    events = []
    active = True

    def guard(event, details):
        if active and event in ("open", "subprocess.Popen", "socket.connect"):
            events.append(event)
            raise RuntimeError("external operation during collected surface clone replay")

    addaudithook(guard)
    try:
        source_file = make_feature_file(part)
        source_fields = source_file.FieldsValue
        source_fields["f60"] = part.HeaderValue.FieldsValue["f48"]
        source_fields["f78"] = 11 * args.variant
        surfaces = cylinder_surface_identities(attachment, source_file)
        clones = tuple(clone_collected_surface(surface.representation) for surface in surfaces)
        new_files = tuple(surface_owner(clone) for clone in clones)
        assert len({id(node) for node in (*new_files, source_file)}) == 4
        assert all(node.FieldsValue["shared"] is source_fields["shared"] for node in new_files)
        assert all(node.FieldsValue["refcfg"] == source_fields["refcfg"]
                   and node.FieldsValue["refcfg"] is not source_fields["refcfg"] for node in new_files)
        fields = finalized_part_prefix(part, 1) | {field.NameValue: [] for field in COLLECTIONS}
        fields |= {"f30": "", "f38_high": 0, "f38_low": 0, "f40": [{"object": node} for node in clones]}
        cache = ArchiveNode(ROOT, fields)
        state = ConfigurationCache(config, True, False, True, cache, False)
        streams = store_part_caches(part.StreamsValue, (state,))
        container = BuildSldprt(streams, FormatVersion=4)
        file = SldprtArchive.from_bytes(container)
        assert all(file.require(name) == raw for name, raw in part.StreamsValue.items())
        raw = file.require(cache_path(config))
        loaded, maps = read_component_body(raw)
        assert write_component_body(loaded)[0] == raw
        files = tuple(surface_owner(entry["object"]) for entry in loaded.FieldsValue["f40"])
        assert len({id(file) for file in files}) == 3
        assert all(file.FieldsValue["f60"] == 0 and file.FieldsValue["f78"] == -1 for file in files)
        source_cfg = source_fields["refcfg"]
        assert all(file.FieldsValue["refcfg"]["f10"] == source_cfg["f10"]
                   and file.FieldsValue["refcfg"]["f08"] == source_cfg["f08"].TextValue
                   for file in files)
        for name in ("h10", "h18"):
            assert len({id(file.FieldsValue["shared"][name]) for file in files}) == 1
        assert source_fields["f60"] != 0 and source_fields["f78"] == 11 * args.variant
        slots = [slot.IndexValue for slot in maps.EntriesValue if any(slot.EntryValue is file for file in files)]
        assert len(slots) == 3
    finally:
        active = False
    print(dumps({
        "passed": True, "variant": args.variant, "cache_bytes": len(raw),
        "cache_sha256": sha256(raw).hexdigest(), "container_sha256": sha256(container).hexdigest(),
        "cloned_file_slots": slots, "map_counter": maps.CounterValue, "source_file_index": source_fields["f78"],
        "saved_file_index": -1, "saved_copy_epoch": 0, "preserved_part_streams": len(part.StreamsValue),
        "runtime_io_attempts": len(events), "native_runs": 0,
        "scope": "collector clone semantics in a scoped typed cylinder cache",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
