# independent expected strings make byte identity observable after source decoding
def AnsiRecord() -> list[dict[str, object]]:
    return [
        {
            "tag": ["ObjectRef", 1],
            "label": ["\xe9\xff", False],
            "vendor_count": 0,
            "framework_count": 0,
            "rows": [
                [["Null", None], ["\x80r", False], -10, 3.25, 0.5],
            ],
        }
    ]
