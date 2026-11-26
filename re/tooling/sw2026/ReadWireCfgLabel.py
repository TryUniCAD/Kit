from struct import calcsize, pack, unpack

from ReadWireCfgFont import CHARACTER, WIDTH, CHAR_FORMAT, read_reference, take_short_text

LABELS = "moLabelDefs_c"
BASE = "moDrViewLabelData_c"
LAYER_MASK = 0x40000000
FIRST_SELECTOR_END = 54
BASE_ORDER = ("f8", "fc", "f18", "f14", "f1c", "f20", "f24", "f28", "f44", "f2c", "f38", "f48")
CHAR_OWNERS = ("f98", "fa0", "fa8", "fb0", "fb8", "fc0")
SUFFIXES = (
    ("f18", "moDetailLabelData_c", "<Ii", ("fcc", "fc8")),
    ("fe8", "moSectionLabelData_c", "<3d5i", ("fc8", "fd0", "fd8", "fe0", "fe4", "fec", "ff0", "fe8")),
    ("f1e8", "moAuxLabelData_c", "<i", ("fc8",)),
    ("f2b8", "moOrthoLabelData_c", "<2i", ("fc8", "fcc")),
    ("f388", "moMiscLabelData_c", "<2i", ("fc8", "fcc")),
)


class LabelBytes:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def take(self, size):
        start = self.offset
        self.offset += size
        if self.offset > len(self.data):
            raise ValueError("reference label record is truncated")
        return self.data[start:self.offset]

    def numbers(self, fmt, keys):
        return dict(zip(keys, unpack(fmt, self.take(calcsize(fmt))), strict=True))

    def text(self):
        value, count = take_short_text(self.data[self.offset:])
        self.take(count)
        return value

    def char_format(self):
        _, count = take_short_text(self.data[self.offset:])
        return read_reference(self.take(count + calcsize(CHAR_FORMAT)), CHARACTER)

    def label_base(self, conditions):
        values = self.numbers("<11ih", BASE_ORDER)
        if conditions & LAYER_MASK and values["f48"] != -1:
            raise ValueError("reference has a conditional layer object")
        values["f88"], values["f90"] = self.text(), self.text()
        values.update(self.numbers("<Iii", ("f5c", "f10", "f58")))
        for name in CHAR_OWNERS[:2]:
            values[name] = self.char_format()
        for name in ("f30", "f3c"):
            values[name] = read_reference(self.take(6), WIDTH)
        for name in CHAR_OWNERS[2:]:
            values[name] = self.char_format()
        return values


def read_label_reference(data, conditions):
    cursor = LabelBytes(data)
    fields = cursor.numbers("<2i", ("f8", "fc"))
    children = []
    for index, (key, layout, fmt, suffix_keys) in enumerate(SUFFIXES):
        if index == 3:
            fields["f458"] = cursor.char_format()
        start = cursor.offset
        child = cursor.label_base(conditions)
        base_end = cursor.offset
        child.update(cursor.numbers(fmt, suffix_keys))
        fields[key] = child
        children.append((layout, start, base_end, cursor.offset))
    if cursor.offset != len(data):
        raise ValueError("reference label record has trailing data")
    return fields, children


def wide_text(text):
    value = text.encode("utf-16-le")
    return b"\xff\xfe\xff" + bytes((len(value) // 2,)) + value


def ansi_text(text):
    value = text.encode("latin-1")
    return bytes((len(value),)) + value


def author_character(seed):
    return wide_text(f"Å{seed}𐐷") + pack(
        CHAR_FORMAT, 0.03125 * seed, -seed, -2.5 * seed, 0xC0000000 + seed,
        0.125 * seed, -5.0 + seed, 6.0 + seed, -17.5 - seed, 11.0 + seed, 0xB0000000 + seed,
    )


def author_base(seed, selector):
    prefix = pack("<11ih", *((-471 + index * 17) * seed for index in range(11)), selector)
    text = wide_text(f"View {seed} Ω") + ansi_text(f"Côté {seed}")
    numbers = pack("<Iii", 0xEC000009 + seed, -76 * seed, 137 * seed)
    chars = [author_character(9 * seed + index) for index in range(6)]
    widths = pack("<hfhf", -30 * seed, 0.125 * seed, 16 * seed, -0.0625 * seed)
    return prefix + text + numbers + b"".join(chars[:2]) + widths + b"".join(chars[2:])


def author_labels(selectors):
    data = bytearray(pack("<2i", -9823, 67751))
    suffixes = [(0xD137ABEA, -71), (-0.5, 4.125, 8.0625, 9, -8, 7, -6, 5),
                (-113,), (631, -737), (-1735, 916)]
    for index, (_, _, fmt, _), selector, suffix in zip(range(5), SUFFIXES, selectors, suffixes, strict=True):
        if index == 3:
            data.extend(author_character(73))
        data.extend(author_base(index + 1, selector))
        data.extend(pack(fmt, *suffix))
    return bytes(data)


def authored_controls():
    labels = author_labels((-2, -1, 0, 37, -32768))
    sentinel = author_labels((-1,) * 5)
    return (("clear_condition", labels, 0), ("other_bit", labels, 0x20000000),
            ("signed_sentinel", sentinel, LAYER_MASK))


def malformed_controls(labels, children):
    active = labels[:FIRST_SELECTOR_END] + pack("<H", 3) + labels[FIRST_SELECTOR_END:]
    active_zero = active[:FIRST_SELECTOR_END - 2] + pack("<h", 0) + active[FIRST_SELECTOR_END:]
    detail_tail = children[0][3]
    store_tail = children[-1][3]
    layer_reason = "moDrViewLabelData_c.f50 layer object"
    return (
        ("active_layer_alias", active, LAYER_MASK, 19000, layer_reason, FIRST_SELECTOR_END),
        ("active_zero_selector", active_zero, LAYER_MASK, 19000, layer_reason, FIRST_SELECTOR_END),
        ("active_layer_truncated", active[:FIRST_SELECTOR_END], LAYER_MASK, 19000, layer_reason, FIRST_SELECTOR_END),
        ("truncated_selector", labels[:FIRST_SELECTOR_END - 1], 0, 19000, "field f18/moDrViewLabelData_c/f48", 52),
        ("truncated_wide_text", labels[:FIRST_SELECTOR_END + 5], 0, 19000, "string payload is truncated", 54),
        ("truncated_detail_suffix", labels[:detail_tail - 1], 0, 19000, "field f18/fc8", detail_tail - 4),
        ("truncated_misc_suffix", labels[:store_tail - 1], 0, 19000, "field f388/fcc", store_tail - 4),
        ("trailing_label_data", labels + b"\x00", 0, 19000, "trailing data", store_tail),
        ("wrong_archive_version", active, LAYER_MASK, 18900, "requires archive version 19000", 0),
    )
