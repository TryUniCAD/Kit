from struct import Struct


BASE_NAMES = (
    "f0c", "f10", "f18", "f20", "f24", "f30", "f28",
    "f6c", "f70", "f74", "f88", "f7c", "f08",
)
BASE = Struct("<iidiidiiiidHi")
SUFFIX_WORD = {
    "moAngleUserUnits_c", "moEnergyUnits_c", "moForceUnits_c",
    "moLengthUserUnits_c", "moPowerUnits_c", "moTimeUnits_c", "moUnitSysUnits_c",
}
DENSITY_NAMES = ("fc0", "fc4", "has_fb8", "fc8", "fcc")


class UnitWire:
    def __init__(self, payload, counter, classes):
        self.payload = payload
        self.counter = counter
        self.classes = dict(classes)
        self.offset = 0

    def scalar_group(self, layout):
        values = layout.unpack_from(self.payload, self.offset)
        self.offset += layout.size
        return values

    def node(self, depth=1):
        start = self.offset
        (tag,) = self.scalar_group(Struct("<H"))
        if tag == 0:
            return None
        if tag == 0xFFFF:
            schema, width = self.scalar_group(Struct("<HH"))
            name = self.payload[self.offset : self.offset + width].decode("ascii")
            if not width or len(name) != width:
                raise ValueError("incomplete reference unit descriptor")
            self.offset += width
            self.classes[self.counter] = name, schema
            self.counter += 1
        elif tag & 0x8000:
            name, schema = self.classes[tag & 0x7FFF]
        else:
            raise ValueError("reference unit record requires a concrete body")
        index = self.counter
        self.counter += 1
        if name == "moUnitsTable_c" and depth == 1:
            (count,) = self.scalar_group(Struct("<H"))
            if count != 16:
                raise ValueError("reference table has an unexpected count")
            fields = {"n": count, "items": [{"o": self.node(2)} for _ in range(count)]}
        elif depth in (2, 3):
            fields = dict(zip(BASE_NAMES, self.scalar_group(BASE), strict=True))
            if name in SUFFIX_WORD:
                (fields["fb0"],) = self.scalar_group(Struct("<H"))
            if name == "moLengthUserUnits_c":
                if depth == 3 and self.payload[self.offset : self.offset + 2] != b"\0\0":
                    raise ValueError("reference length override must be terminal")
                fields["fb8"] = self.node(depth + 1)
            if name == "moDensityUnits_c":
                fields.update(
                    zip(DENSITY_NAMES, self.scalar_group(Struct("<HHBHi")), strict=True)
                )
                if fields["has_fb8"]:
                    raise ValueError("reference density has an unexpected override")
        else:
            raise ValueError("unexpected unit body in reference table")
        return name, schema, index, start, self.offset, fields


def read_wire_units(payload, counter, classes):
    wire = UnitWire(payload, counter, classes)
    graph = wire.node()
    if graph is None or wire.offset != len(payload):
        raise ValueError("reference unit table does not consume the full record")
    return graph, wire.counter, wire.classes
