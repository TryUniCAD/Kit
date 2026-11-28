from hashlib import sha256
from json import dumps
from struct import pack
from sys import addaudithook

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from downstream.Body import (
    COLLECTIONS, IDENTITY_TABLES, PREFIX, ROOT, TABLE_KINDS, UNIQUE, isolated_body_context,
    read_standalone_body, write_standalone_body,
)


def map_shape(snapshot):
    return [
        (slot.IndexValue, slot.EntryValue.ClassValue, slot.EntryValue.FieldsValue)
        if isinstance(slot.EntryValue, ArchiveNode) else (slot.IndexValue, slot.EntryValue)
        for slot in snapshot.EntriesValue
    ]


def roundtrip(node):
    raw, before = write_standalone_body(node, isolated_body_context())
    loaded, after = read_standalone_body(raw, isolated_body_context())
    emitted, repeated = write_standalone_body(loaded, isolated_body_context())
    assert emitted == raw
    assert before.CounterValue == after.CounterValue == repeated.CounterValue
    assert map_shape(before) == map_shape(after)
    assert after.EntriesValue == repeated.EntriesValue
    return raw, loaded, after


def main():
    expected = {field.NameValue for field in COLLECTIONS}
    assert len(expected) == 18
    values = {name: ordinal for ordinal, name in enumerate(PREFIX, 1)}
    values["f28"] = 0xffffffff
    values |= {key: [] for key in expected}
    values |= {"f30": ("A", ""), "f38_high": 0, "f38_low": 0}
    plain = ArchiveNode(ROOT, values)
    empty, _, empty_map = roundtrip(plain)
    assert empty == pack("<8I", *[values[name] for name in PREFIX]) + bytes(17 * 4 + 1 + 8 + 4)
    assert len(empty) == 113 and empty_map.CounterValue == 1 and empty_map.EntriesValue == ()

    entity = ArchiveNode(UNIQUE, {"f08": -7, "f0c": 390175, "f10": -19, "high": 3742, "low": 4251})
    new_values = {**values}
    for i, field in enumerate(COLLECTIONS, 1):
        if field.NameValue in TABLE_KINDS:
            candidate = {"key": -i, "object": None, "word": 1000 + i}
            new_values[field.NameValue] = [{rule.NameValue: candidate[rule.NameValue] for rule in field.BodyValue}]
    for index, key in enumerate(IDENTITY_TABLES, 1):
        key_word = index if index == 1 else -index
        new_values[key] = [{"key": 0}, {"key": key_word, "object": entity}]
    new_values["f540"] = [{"member": -102}, {"member": 309}]
    new_values["f650"] = [{"key": 3, "x": 0.0125, "y": -0.0475, "z": 0.00078125}]
    new_values |= {"f30": ("A", "60e4e062-a5d2-504e-90ca-a4ed0a3760fe"), "f38_high": 642, "f38_low": 528}
    populated = ArchiveNode(ROOT, new_values)
    raw, recovered, body_map = roundtrip(populated)
    recovered_ids = [recovered.FieldsValue[section][1]["object"] for section in IDENTITY_TABLES]
    assert len({id(value) for value in recovered_ids}) == 1 and body_map.CounterValue == 3
    assert all(value.ClassValue == UNIQUE for value in recovered_ids)
    class_slot, object_slot = body_map.EntriesValue
    assert (class_slot.IndexValue, class_slot.EntryValue) == (1, UNIQUE)
    assert object_slot.IndexValue == 2 and object_slot.EntryValue is recovered_ids[0]
    assert all(recovered.FieldsValue[f"{name}#count"] == len(new_values[name]) for name in expected)
    assert recovered.FieldsValue["f650"][0] == new_values["f650"][0]
    assert pack("<iiiII", -7, 390175, -19, 3742, 4251) in raw
    identity = new_values["f30"][1]
    wide_node = ArchiveNode(ROOT, {**new_values, "f30": identity})
    wide, wide_body, _ = roundtrip(wide_node)
    ansi_frame = pack("<B", len(identity)) + identity.encode("ascii")
    wide_frame = pack("<BHB", 0xff, 0xfffe, len(identity)) + identity.encode("utf-16-le")
    assert raw.count(ansi_frame) == 1
    assert wide == raw.replace(ansi_frame, wide_frame, 1)
    assert wide_body.FieldsValue["f30"] == identity

    negative = empty[:32] + pack("<i", -1) + empty[36:]
    controls = {}
    checks = {
        "negative_count": negative,
        "trailing_byte": raw + b"\x01",
        "truncated_point": raw[:-1],
    }
    for label, invalid in checks.items():
        try:
            read_standalone_body(invalid, isolated_body_context())
        except ValueError as error:
            controls[label] = type(error).__name__
        else:
            raise AssertionError(f"accepted {label}")

    for key, bad in (("zero_with_pointer", {"key": 0, "object": entity}), ("nonzero_without_pointer", {"key": 1})):
        forged = ArchiveNode(ROOT, {**new_values, "f340": [bad]})
        try:
            write_standalone_body(forged, isolated_body_context())
        except ValueError as error:
            controls[key] = type(error).__name__
        else:
            raise AssertionError(f"accepted {key}")
    for label, fields in (
        ("foreign_pointer_type", {**new_values, "f60": [{"object": entity, "word": 12}]}),
        ("unknown_body_field", {**new_values, "non_wire_data": 123}),
    ):
        try:
            write_standalone_body(ArchiveNode(ROOT, fields), isolated_body_context())
        except ValueError as error:
            controls[label] = type(error).__name__
        else:
            raise AssertionError(f"accepted {label}")

    bad_context = isolated_body_context()
    bad_context.FlagsValue["conditions"] = 0x80
    try:
        read_standalone_body(raw, bad_context)
    except ValueError as error:
        controls["embedded_context"] = type(error).__name__
    else:
        raise AssertionError("accepted embedded context in standalone body")

    import codecs
    for encoding in ("cp1252", "utf-16le", "utf-8"):
        codecs.lookup(encoding)
    attempts = []
    active = True
    def guard(event, values):
        if active and event in ("open", "subprocess.Popen", "socket.connect"):
            attempts.append(event)
            raise RuntimeError("downstream body proof used an external operation")
    addaudithook(guard)
    try:
        guarded = ((plain, empty), (populated, raw), (wide_node, wide))
        for node, expected_bytes in guarded:
            again, _, _ = roundtrip(node)
            assert again == expected_bytes
    finally:
        active = False
    print(dumps({
        "passed": True, "empty_bytes": len(empty), "populated_bytes": len(raw),
        "populated_sha256": sha256(raw).hexdigest(), "counted_sections": len(expected),
        "repeated_real_schema_pointers": len(recovered_ids),
        "map_before": empty_map.CounterValue, "map_after": body_map.CounterValue,
        "class_slot": class_slot.IndexValue, "object_slot": object_slot.IndexValue,
        "wide_cstring_bytes": len(wide), "wide_cstring_sha256": sha256(wide).hexdigest(),
        "independent_primitive_framing_checks": 3, "malformed_refusals": controls,
        "guarded_payloads": len(guarded), "runtime_io_attempts": len(attempts), "native_runs": 0,
        "scope": "standalone direct-body grammar with modeled values and fresh logical map",
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
