from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps
from pathlib import PureWindowsPath
from sys import addaudithook

from FreshCylinderInput import make_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from downstream.CheckReferences import make_body
from downstream.Components import read_component_body, write_component_body
from downstream.Storage import ConfigurationCache, cache_path, configuration_storage_name, store_part_caches


def prepare_part():
    name = "DownstreamArchiveStorage"
    document = make_document({
        "name": name, "axis": "z", "plane": "Front Plane", "center_mm": (4.5, -7.125),
        "radius_mm": 5.25, "depth_mm": 19.75, "driver": "diameter", "reversed": False,
    })
    document.AssertValid()
    return PrepareNative(document, BytesIO(), 1818199455, WriteOptions(
        values={"final_destination": str(PureWindowsPath("C:/KitResearch", name + ".SLDPRT"))},
    ))


def main():
    for encoding in ("latin-1", "cp1252", "utf-16le", "utf-16be", "utf-8"):
        lookup(encoding)
    part = prepare_part()
    config = part.CurrentConfig
    assert config.FieldsValue["owner"] is part.SystemValue.RootValue
    config_id = config.FieldsValue["f08"]
    fresh = ConfigurationCache(config_id, True, False, True, make_body(False), False)
    extra = ConfigurationCache((12, 9), True, False, False, make_body(False), False)
    extra.cache.FieldsValue["f540"] = [{"member": 37}, {"member": 149}, {"member": 508}]
    events = []
    active = True

    def guard(event, args):
        if active and event in ("open", "subprocess.Popen", "socket.connect"):
            events.append(event)
            raise RuntimeError("external operation during downstream stream construction")

    addaudithook(guard)
    try:
        primary_name = cache_path(config_id)
        assert configuration_storage_name(config_id) == "Config-0"
        assert configuration_storage_name(-17) == "Config--17"
        assert configuration_storage_name((12, 9)) == "FlexCfg-12-9"
        assert configuration_storage_name((-4, 52)) == "FlexCfg--4-52"
        initial = dict(part.StreamsValue)
        current = store_part_caches(initial, (fresh,))
        assert len(current) == len(initial) + 1 and all(current[name] == value for name, value in initial.items())
        assert primary_name not in initial
        encapsulated = BuildSldprt(current, FormatVersion=4)
        inspected = SldprtArchive.from_bytes(encapsulated)
        assert inspected.streams == current
        raw = inspected.require(primary_name)
        recovered, snapshot = read_component_body(raw)
        assert write_component_body(recovered)[0] == raw and snapshot.CounterValue == 23
        assert BuildSldprt(inspected.streams, FormatVersion=4) == encapsulated

        for skipped in (replace(fresh, needs_rebuild=True, is_current=False), replace(fresh, opened_model=False)):
            assert store_part_caches(current, (skipped,)) == current
        for stale in (replace(fresh, cache=None), replace(fresh, cache_needs_update=True)):
            assert store_part_caches(current, (stale,)) == initial
        assert store_part_caches(initial, (replace(fresh, needs_rebuild=True),)) == current

        both = store_part_caches({}, (replace(fresh, storage_id=42), extra))
        names = (cache_path(42), cache_path((12, 9)))
        assert tuple(both) == names
        assert len(both[names[1]]) - len(both[names[0]]) == 12
        envelope = BuildSldprt(both, FormatVersion=4)
        reopened = SldprtArchive.from_bytes(envelope)
        assert reopened.streams == both and len(reopened.records) == 2
        for name in names:
            model, maps = read_component_body(reopened.require(name))
            assert maps.CounterValue == 23 and write_component_body(model)[0] == both[name]
        assert BuildSldprt(reopened.streams, FormatVersion=4) == envelope

        for state in (replace(fresh, storage_id=True), replace(fresh, storage_id=(12, 0x80000000))):
            try:
                store_part_caches(initial, (state,))
            except ValueError:
                pass
            else:
                raise AssertionError("accepted an invalid configuration storage identifier")
        try:
            store_part_caches(initial, (fresh, fresh))
        except ValueError:
            pass
        else:
            raise AssertionError("accepted repeated configuration storage ownership")
        assert initial == dict(part.StreamsValue)
    finally:
        active = False
    print(dumps({
        "passed": True, "generated_part_streams_preserved": len(initial), "modeled_cache_path": primary_name,
        "part_container_sha256": sha256(encapsulated).hexdigest(), "part_container_bytes": len(encapsulated),
        "stream_paths": names, "stream_sizes": [len(both[name]) for name in names],
        "isolated_envelope_sha256": sha256(envelope).hexdigest(),
        "isolated_envelope_bytes": len(envelope), "selection_branches": 6,
        "invalid_inputs_refused": 3, "runtime_io_attempts": len(events), "native_runs": 0,
        "scope": "actual generated part envelope with controlled modeled cache, plus standalone name and branch replay",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
