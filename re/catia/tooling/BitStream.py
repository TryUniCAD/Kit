from __future__ import annotations

import struct

MASK64 = (1 << 64) - 1


class BitWriter:
    def __init__(self) -> None:
        self.buffer = 0
        self.position = 0
        self.output = bytearray()

    def Write(self, value: int, want: int, capacity: int) -> None:
        delta = (self.position - want) & 0xFFFF
        signed = delta - 0x10000 if delta & 0x8000 else delta
        limit = 1 << (capacity if capacity < 64 else 64)
        placed = (
            (value & (limit - 1)) >> signed
            if signed > 0
            else (value << (-signed)) & MASK64
        )
        self.buffer = (self.buffer | placed) & MASK64
        self.position = (delta + capacity) & 0xFFFF
        if self.position > 0x3F:
            self.output += self.buffer.to_bytes(8, "big")
            self.position -= 0x40
            if self.position != 0:
                self.buffer = (value << ((capacity - self.position) & 0x3F)) & MASK64
            else:
                self.buffer = 0

    def Finish(self) -> bytes:
        if self.position > 0:
            self.output += self.buffer.to_bytes(8, "big")
        return bytes(self.output)


class BitReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.buffer = 0
        self.position = 0x40
        self.index = 0

    def Refill(self) -> None:
        chunk = self.data[self.index : self.index + 8]
        self.index += 8
        self.buffer = int.from_bytes(chunk.ljust(8, b"\0"), "big")

    def ReadUncleared(self, want: int, capacity: int) -> int:
        delta = (want - self.position) & 0xFFFF
        guard = (delta + 0x40) & 0xFFFF
        result = 0
        if guard & 0xFF7F:
            signed = delta - 0x10000 if delta & 0x8000 else delta
            result = (
                (self.buffer >> signed)
                if signed > 0
                else ((self.buffer << (-signed)) & MASK64)
            )
        self.position = (self.position + (capacity - want)) & 0xFFFF
        if self.position > 0x40:
            self.Refill()
            self.position -= 0x40
            if self.position != 0:
                result |= self.buffer >> ((capacity - self.position) & 0x3F)
        return result

    def Read(self, want: int, capacity: int) -> int:
        return self.ReadUncleared(want, capacity) & ((1 << want) - 1)


def FloatBits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def BitsFloat(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def LeadingZeros(value: int) -> int:
    return 32 if value == 0 else 32 - value.bit_length()


def RoundTripLiterals(values: tuple[float, ...]) -> tuple[float, ...]:
    writer = BitWriter()
    for value in values:
        writer.Write(FloatBits(value), 0x20, 0x40)
    reader = BitReader(writer.Finish())
    return tuple(BitsFloat(reader.Read(0x20, 0x40)) for _ in values)


def main() -> None:
    values = (0.785398, 7.5, 4.2, -2.5, 1e12)
    got = RoundTripLiterals(values)
    print("literal", [round(item, 4) for item in got])
    print("match", all(abs(a - b) <= 1e-4 * max(1.0, abs(a)) for a, b in zip(values, got)))
    for value in (1, 2, 0x80000000, 0x10000, 0x1000, 0):
        print("clz", hex(value), LeadingZeros(value))


if __name__ == "__main__":
    main()
