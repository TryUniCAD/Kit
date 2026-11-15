"""Research-only decoder for the Creo packed double encoding.

`ugc_ieee_unformat_double` at `0x180101f40` in `coreutils_sh.dll` reads a hex
string where each byte's low nibble is a hex digit. It pairs the digits into
bytes and stores them into the 8-byte output buffer from offset 7 down to 0, so
the first digit pair is the most significant byte. `0x52` (`R`) zeroes the
buffer and returns 1, `0x00` returns 1 (0.0), and `0x2e` (`.`) returns 0.

This module applies that decoder to the `ent_outl` and `envlp` blobs and prints
the result. It is not production code.
"""

from __future__ import annotations

import struct
import sys


def UnformatDouble(blob: bytes, high_nibble: bool = False) -> tuple[float, bytes]:
    digits = [(value >> 4) if high_nibble else (value & 0xF) for value in blob]
    buffer = bytearray(8)
    position = 7
    index = 0
    while index < len(digits) and position >= 0:
        high = digits[index]
        low = digits[index + 1] if index + 1 < len(digits) else 0
        buffer[position] = (high << 4) | low
        position -= 1
        index += 2
    return struct.unpack(">d", bytes(buffer))[0], bytes(buffer)


BLOBS = {
    "empty_ent_outl_1": "466fca906689b97fe4",
    "empty_ent_outl_2": "2d6fca906689b97fe4",
    "ladder_ent_outl_1": "46675cc1f8683c94d52079daf1e902",
    "ladder_ent_outl_2": "2d639a472afc62e42d710b88a1ca5eb3",
    "ladder_envlp_1": "4667104010fc74f0",
    "ladder_envlp_2": "465584469c0fd8e0",
    "ladder_envlp_3": "2d634dc543909b40",
    "ladder_envlp_4": "2d5ce9bee1b54b38",
}


def Main() -> int:
    for name, text in BLOBS.items():
        blob = bytes.fromhex(text)
        for high in (False, True):
            value, buffer = UnformatDouble(blob, high)
            print(f"{name:20s} high={int(high)} buffer={buffer.hex()} value={value!r}")
    return 0


if __name__ == "__main__":
    sys.exit(Main())
