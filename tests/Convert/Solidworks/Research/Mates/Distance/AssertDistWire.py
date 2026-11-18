from typing import cast as CastValue


# packed display storage must be fully typed computed binary doubles with exact native allocation framing rather than unclassified bytes
def AssertDistWire(MateStream: dict[str, object]) -> None:
    for ModeValue in ("read_coverage", "write_coverage"):
        Coverage = CastValue(dict[str, object], MateStream[ModeValue])
        assert Coverage["completed"] is True
        assert not Coverage["missing_schemas"]
        assert not Coverage["provisional_schemas"]
        NativeFields = CastValue(
            list[dict[str, object]], Coverage["native_byte_fields"]
        )
        assert len(NativeFields) == 1
        FieldValue = NativeFields[0]
        assert FieldValue["completed"] is True
        assert FieldValue["schema"] == "dm.FUN_4bd03960"
        assert FieldValue["object_class"] == "moDisplayDistanceDim_c"
        assert FieldValue["element_type"] == "f64"
        assert FieldValue["element_count"] == 1
        assert FieldValue["declared_length"] == FieldValue["observed_length"] == 8
        assert FieldValue["length_rule"] == "count_times_native_binary64_width"
        assert FieldValue["typed_values"] == [0.0]
