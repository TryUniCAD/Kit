from codecs import lookup
from hashlib import sha256
from json import dumps
from sys import addaudithook

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from downstream.CheckReferences import make_body
from downstream.CheckStorage import prepare_part
from downstream.Components import (
    UNIT_COMPONENT_CLASS, make_local_unit_component, read_component_body, write_component_body,
)
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches


def main():
    for encoding in ("utf-8", "utf-16le", "latin-1", "cp1252"):
        lookup(encoding)
    part = prepare_part()
    graph = make_body(False)
    config = part.CurrentConfig
    ids = config.FieldsValue["f08"]
    events = []
    active = True

    def guard(event, args):
        if active and event in ("open", "subprocess.Popen", "socket.connect"):
            events.append(event)
            raise RuntimeError("external operation during local unit clone replay")

    addaudithook(guard)
    try:
        for name in ("f48", "f60"):
            graph.FieldsValue[name][0]["object"].FieldsValue["f58"] = make_local_unit_component(part)
        state = ConfigurationCache(ids, True, False, True, graph, False)
        combined = store_part_caches(part.StreamsValue, (state,))
        container = BuildSldprt(combined, FormatVersion=4)
        file = SldprtArchive.from_bytes(container)
        assert file.streams == combined
        raw = file.require(cache_path(ids))
        read, maps = read_component_body(raw)
        assert write_component_body(read)[0] == raw
        clones = tuple(read.FieldsValue[name][0]["object"].FieldsValue["f58"] for name in ("f48", "f60"))
        assert clones[0] is not clones[1]
        assert all(clone.FieldsValue == {"owner": None, "has_ext": 0} for clone in clones)
        assert all(raw[clone.EndOffset-3:clone.EndOffset] == b"\0\0\0" for clone in clones)
        assert maps.CounterValue == 26
        classes = [item for item in maps.EntriesValue if type(item.EntryValue) is RuntimeClass
                   and item.EntryValue.NameValue == UNIT_COMPONENT_CLASS]
        objects = [item for item in maps.EntriesValue if item.EntryValue in clones]
        assert len(classes) == 1 and len(objects) == 2
        assert all(item.IndexValue > classes[0].IndexValue for item in objects)

        original = graph.FieldsValue["f48"][0]["object"].FieldsValue["f58"]
        original.FieldsValue["owner"] = graph.FieldsValue["f40"][0]["object"]
        try:
            write_component_body(graph)
        except ValueError:
            pass
        else:
            raise AssertionError("accepted a persisted owner on a standalone unit clone")
    finally:
        active = False
    print(dumps({
        "passed": True, "unit_component_class_slot": classes[0].IndexValue,
        "unit_object_slots": [item.IndexValue for item in objects], "per_unit_payload_bytes": 3,
        "object_map_counter": maps.CounterValue, "cache_body_bytes": len(raw),
        "cache_body_sha256": sha256(raw).hexdigest(), "container_sha256": sha256(container).hexdigest(),
        "runtime_io_attempts": len(events), "native_runs": 0,
        "scope": "modeled downstream references with separate generated local unit component clones",
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
