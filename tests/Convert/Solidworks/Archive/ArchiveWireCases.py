# authored input puts count domains and tag widths next to other fields
def AuthoredRecord() -> list[dict[str, object]]:
    return [
        {
            "tag": ["NewClass", None],
            "label": ["a🐈", True],
            "vendor_count": 0xFFFFFFFF,
            "framework_count": 0xFFFFFFFF,
            "rows": [
                [["ClassRef", 0x7FFE], ["", True], -7, 1.5, 2.25],
                [["ObjectRef", 0x7FFF], ["Row", True], 18, -2.5, 0.125],
            ],
        },
        {
            "tag": ["ClassRef", 0x7FFF],
            "label": ["z" * 255, True],
            "vendor_count": 0xFFFE,
            "framework_count": 0xFFFFFFFE,
            "rows": [
                [["ObjectRef", 2], ["z" * 65532 + "\U0001f408", True], 120, 0.25, 0.5],
                [["Null", None], ["x", True], -2147483648, 0.5, -1.0],
            ],
        },
    ]
