from tests.Convert.Solidworks.Archive.CanonicalWire import KWireHeader


# deliberate wire breaks distinguish ownership errors from unrelated process failures
def BrokenRecords(PayloadValue: bytes) -> tuple[tuple[str, bytes, str], ...]:
    BodyValue = PayloadValue[len(KWireHeader) :]
    return (
        (
            "ScalarOffset",
            b"\xfc\xff\xff\xff" + PayloadValue[4:],
            "archive scalar position must be nonnegative",
        ),
        (
            "BoundedCount",
            KWireHeader + b"\xff" * 6 + BodyValue[2:],
            "archive count exceeds the remaining stream size at byte 8",
        ),
        (
            "Count",
            KWireHeader + b"\xff\xff\x01",
            "archive count has no complete unsigned long at byte 8",
        ),
        (
            "MfcCount",
            KWireHeader + BodyValue[:27],
            "framework count has no complete unsigned long long",
        ),
        (
            "Tag",
            KWireHeader + BodyValue[:2] + b"\x00\x80" + BodyValue[4:],
            "archive class reference cannot use reserved index zero",
        ),
        (
            "String",
            KWireHeader + BodyValue[:7] + b"\xff\xfe\xff" + BodyValue[7:],
            "archive string repeats the Unicode marker",
        ),
        ("Scalar", PayloadValue[:-1], "truncated SOLIDWORKS archive field"),
        (
            "Tail",
            PayloadValue + b"\x00",
            "synthetic archive record retains unread bytes",
        ),
    )
