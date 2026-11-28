from dataclasses import dataclass
from struct import unpack


@dataclass(frozen=True, slots=True)
class ExchangeMap:
    pairs: tuple

    def values(self, name):
        return tuple(value for key, value in self.pairs if key == name)

    def field(self, name):
        values = self.values(name)
        if len(values) != 1:
            raise ValueError("exchange map requires one actual " + name)
        return values[0]


class ExchangeReader:
    def __init__(self, payload):
        self.payload = payload
        self.offset = 0

    def take(self, count):
        end = self.offset + count
        if end > len(self.payload):
            raise ValueError("truncated exchange MessagePack value")
        data = self.payload[self.offset:end]
        self.offset = end
        return data

    def integer(self, count, *, signed=False):
        return int.from_bytes(self.take(count), "big", signed=signed)

    def items(self, count, depth, *, mapping=False):
        if count * (2 if mapping else 1) > len(self.payload) - self.offset:
            raise ValueError("truncated exchange MessagePack collection")
        if not mapping:
            return tuple(self.value(depth) for _ in range(count))
        pairs = tuple((self.value(depth), self.value(depth)) for _ in range(count))
        if any(type(key) is not str for key, _ in pairs):
            raise ValueError("exchange MessagePack map requires text keys")
        return ExchangeMap(pairs)

    def value(self, depth=0):
        if depth > 16:
            raise ValueError("unsupported exchange MessagePack nesting")
        tag = self.integer(1)
        if tag < 0x80:
            return tag
        if tag >= 0xE0:
            return tag - 0x100
        if tag <= 0x8F:
            return self.items(tag - 0x80, depth + 1, mapping=True)
        if tag <= 0x9F:
            return self.items(tag - 0x90, depth + 1)
        if tag <= 0xBF:
            return self.take(tag - 0xA0).decode("utf-8")
        if tag in (0xC2, 0xC3):
            return tag == 0xC3
        if tag == 0xCB:
            return unpack(">d", self.take(8))[0]
        if 0xCC <= tag <= 0xCF:
            return self.integer(1 << (tag - 0xCC))
        if 0xD0 <= tag <= 0xD3:
            return self.integer(1 << (tag - 0xD0), signed=True)
        if 0xD9 <= tag <= 0xDB:
            return self.take(self.integer(1 << (tag - 0xD9))).decode("utf-8")
        if 0xDC <= tag <= 0xDF:
            count = self.integer(2 if tag % 2 == 0 else 4)
            return self.items(count, depth + 1, mapping=tag >= 0xDE)
        raise ValueError("unsupported exchange MessagePack atom")


def read_exchange_map(payload):
    if type(payload) is not bytes or not payload:
        raise ValueError("exchange map requires an owned MessagePack payload")
    reader = ExchangeReader(payload)
    value = reader.value()
    if type(value) is not ExchangeMap or reader.offset != len(payload):
        raise ValueError("exchange cell must contain one complete MessagePack map")
    return value


def encode_config_atom(value):
    if type(value) is str:
        raw = value.encode("utf-8")
        size = len(raw)
        if size < 32:
            return bytes((0xA0 + size,)) + raw
        if size < 256:
            return bytes((0xD9, size)) + raw
        if size < 65536:
            return b"\xda" + size.to_bytes(2, "big") + raw
    if type(value) is int:
        if -32 <= value < 128:
            return bytes((value & 0xFF,))
        for width, code in ((1, 0xCC), (2, 0xCD), (4, 0xCE)):
            if 0 <= value < 1 << (8 * width):
                return bytes((code,)) + value.to_bytes(width, "big")
    raise ValueError("unsupported ordinary configuration MessagePack atom")
