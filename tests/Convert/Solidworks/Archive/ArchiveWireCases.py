from struct import pack as PackValues


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
                [["Null", None], ["x", True], -2147483648, 0.5, -1.0],
            ],
        },
    ]


# an independent wire expectation catches matching mistakes in both processes
def CanonicalWire() -> bytes:
    return b"".join(
        (
            b"\x02\x00\xff\xff",
            b"\xff\xfe\xff\x03a\x00\x3d\xd8\x08\xdc",
            b"\xff" * 6,
            b"\xff" * 10 + b"\x00" * 4,
            b"\x02\x00",
            b"\xfe\xff\xff\xfe\xff\x00",
            PackValues("<ifd", -7, 1.5, 2.25),
            b"\xff\x7f\xff\x7f\x00\x00",
            b"\xff\xfe\xff\x03R\x00o\x00w\x00",
            PackValues("<ifd", 18, -2.5, 0.125),
            b"\xff\x7f\xff\x7f\x00\x80",
            b"\xff\xfe\xff\xff\xff\x00" + b"z\x00" * 255,
            b"\xfe\xff\xff\xff\xfe\xff\xff\xff\x01\x00",
            b"\x00\x00\xff\xfe\xff\x01x\x00",
            PackValues("<ifd", -2147483648, 0.5, -1.0),
        )
    )


# deliberate wire breaks distinguish ownership errors from unrelated process failures
def BrokenRecords(PayloadValue: bytes) -> tuple[tuple[str, bytes, str], ...]:
    return (
        ("Count", b"\xff\xff\x01", "archive count has no complete unsigned long"),
        (
            "MfcCount",
            PayloadValue[:27],
            "framework count has no complete unsigned long long",
        ),
        (
            "Tag",
            PayloadValue[:2] + b"\x00\x80" + PayloadValue[4:],
            "archive class reference cannot use reserved index zero",
        ),
        (
            "String",
            PayloadValue[:7] + b"\xff\xfe\xff" + PayloadValue[7:],
            "archive string repeats the Unicode marker",
        ),
        ("Scalar", PayloadValue[:-1], "truncated SOLIDWORKS archive field"),
        (
            "Tail",
            PayloadValue + b"\x00",
            "synthetic archive record retains unread bytes",
        ),
    )
