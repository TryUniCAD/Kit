from struct import Struct, pack


PRE_FIELDS = (
    "f20", "f28", "f30", "f10", "f08", "f18", "f38", "f40",
    "f48", "f50", "f60", "f58", "f1c0", "f1c4", "f1c8", "f1cc",
    "f1e0", "f00", "f134", "f138", "f13c", "f140",
)


class CacheWire:
    def __init__(self, payload):
        self.payload = payload
        self.offset = 0

    def take(self, fmt):
        width = Struct(fmt)
        result = width.unpack_from(self.payload, self.offset)
        self.offset += width.size
        return result

    def text(self):
        (width,) = self.take("<B")
        wide = width == 255
        if wide:
            marker, width = self.take("<HB")
            if marker != 0xFFFE or width == 255:
                raise ValueError("unexpected cache reference text prefix")
        size = width * (2 if wide else 1)
        (data,) = self.take(f"<{size}s")
        return data.decode("utf-16-le") if wide else ("A", data.decode("cp1252"))


def mass_properties(wire):
    fields = dict(zip(PRE_FIELDS, wire.take("<12d5id4i"), strict=True))
    fields["f148"] = wire.text()
    fields["f150"] = wire.text()
    tail = wire.take("<i12diH")
    fields["f1f0"] = tail[0]
    fields.update(zip(("fc8", "fd0", "fd8"), tail[1:4], strict=True))
    for index, name in enumerate(("f68", "f80", "f98"), 1):
        start = 1 + 3 * index
        fields[name] = dict(zip(("x", "y", "z"), tail[start : start + 3], strict=True))
    fields["f15c"], fields["f128"] = tail[-2:]
    return fields


def read_mass_wire(payload):
    wire = CacheWire(payload)
    (count,) = wire.take("<i")
    if not 0 <= count <= 2:
        raise ValueError("unsupported cache reference count")
    slots = []
    for _ in range(count):
        (row_count,) = wire.take("<i")
        if not 0 <= row_count <= 2:
            raise ValueError("reference cache row count exceeds its controls")
        rows = [
            dict(zip(("atom", "v", "d"), wire.take("<iid"), strict=True))
            for _ in range(row_count)
        ]
        slot = {"n10": row_count, "f08": rows}
        if rows:
            slot["f18"] = mass_properties(wire)
        slots.append(slot)
    selector = wire.take("<i")[0] if count == 2 else 0
    if wire.offset != len(payload):
        raise ValueError("cache reference has trailing data")
    return {"f1628": slots, "f1638": selector}


def author_mass_wire():
    start = pack("<12d5id4i", *(
        [0.25 + index / 8 for index in range(12)]
        + [4, -8, 16, -32, 64]
        + [0.5]
        + [6, 7, 8, 9]
    ))
    ansi = b"rendered cache"
    wide = "edited β".encode("utf-16-le")
    texts = pack("<B", len(ansi)) + ansi + pack("<BHB", 255, 0xFFFE, len(wide) // 2) + wide
    end = pack("<i12diH", -3, *(index / 4 for index in range(12)), -6, 7)
    atoms = pack("<iidiid", 101, -5, 0.125, 103, 7, 0.875)
    return pack("<iii", 2, 0, 2) + atoms + start + texts + end + pack("<i", -17)
