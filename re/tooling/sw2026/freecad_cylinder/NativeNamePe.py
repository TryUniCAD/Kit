from hashlib import sha256
from struct import unpack_from


def require(value, reason):
    if not value:
        raise ValueError(reason)


class NativeNamePe:
    def __init__(self, data):
        self.data = data
        self.sha256 = sha256(data).hexdigest()
        self.pe = unpack_from("<I", data, 0x3C)[0]
        require(data[self.pe:self.pe + 4] == b"PE\0\0", "name resource input is not PE")
        self.machine = unpack_from("<H", data, self.pe + 4)[0]
        count = unpack_from("<H", data, self.pe + 6)[0]
        size = unpack_from("<H", data, self.pe + 20)[0]
        self.optional = self.pe + 24
        require(unpack_from("<H", data, self.optional)[0] == 0x20B, "name resource scope requires PE32+")
        self.base = unpack_from("<Q", data, self.optional + 24)[0]
        self.sections = []
        for index in range(count):
            offset = self.optional + size + index * 40
            _, rva, length, raw = unpack_from("<IIII", data, offset + 8)
            self.sections.append((rva, length, raw))

    def offset(self, rva, size=1):
        if 0 <= rva and rva + size <= 0x1000:
            return rva
        for begin, length, raw in self.sections:
            if begin <= rva and rva + size <= begin + length:
                return raw + rva - begin
        raise ValueError("native name address is outside the original file-backed image")

    def ascii(self, rva):
        offset = self.offset(rva)
        end = self.data.index(b"\0", offset)
        return self.data[offset:end].decode("ascii")

    def imports(self):
        rva, _ = unpack_from("<II", self.data, self.optional + 112 + 8)
        values, index = {}, 0
        while rva:
            offset = self.offset(rva) + index * 20
            original, stamp, chain, name, first = unpack_from("<IIIII", self.data, offset)
            index += 1
            if not any((original, stamp, chain, name, first)):
                break
            module = self.ascii(name)
            entry = 0
            while True:
                value = unpack_from("<Q", self.data, self.offset(original or first) + entry * 8)[0]
                if not value:
                    break
                values[self.base + first + entry * 8] = {
                    "module": module, "ordinal": (value & 0xFFFF) if value >> 63 else None,
                    "name": None if value >> 63 else self.ascii(value + 2),
                }
                entry += 1
        return values

    def ordinal(self, number):
        rva, length = unpack_from("<II", self.data, self.optional + 112)
        offset = self.offset(rva)
        base, count, _, address_table = unpack_from("<IIII", self.data, offset + 16)
        require(base <= number < base + count, "MFC ordinal is absent from the selected view")
        target = unpack_from("<I", self.data, self.offset(address_table) + (number - base) * 4)[0]
        return {"ordinal": number, "rva": target, "address": hex(self.base + target),
                "forward": self.ascii(target) if rva <= target < rva + length else None}

    def resource(self, resource_id):
        rva, _ = unpack_from("<II", self.data, self.optional + 112 + 2 * 8)
        if not rva:
            return []
        root = self.offset(rva)

        def entries(relative):
            offset = root + relative
            named, ids = unpack_from("<HH", self.data, offset + 12)
            return [unpack_from("<II", self.data, offset + 16 + index * 8) for index in range(named + ids)]

        rows = []
        for kind, type_pointer in entries(0):
            if kind != 6:
                continue
            require(type_pointer >> 31, "RT_STRING type has no resource directory")
            for name, name_pointer in entries(type_pointer & 0x7FFFFFFF):
                if name != (resource_id >> 4) + 1:
                    continue
                require(name_pointer >> 31, "RT_STRING block has no language directory")
                for language, leaf in entries(name_pointer & 0x7FFFFFFF):
                    require(leaf >> 31 == 0, "RT_STRING language is not a data entry")
                    address, length, code_page, reserved = unpack_from("<IIII", self.data, root + leaf)
                    offset = self.offset(address, length)
                    payload = self.data[offset:offset + length]
                    cursor, target = 0, None
                    for index in range(16):
                        count = unpack_from("<H", payload, cursor)[0]
                        cursor += 2
                        require(cursor + count * 2 <= len(payload), "RT_STRING text exceeds its owned block")
                        text = payload[cursor:cursor + count * 2].decode("utf-16-le")
                        cursor += count * 2
                        if index == (resource_id & 15):
                            target = text
                    require(target is not None, "selected name resource has no string slot")
                    rows.append({"language_id": language, "value": target, "block_id": name,
                                 "slot": resource_id & 15, "payload_rva": address, "payload_bytes": length,
                                 "payload_sha256": sha256(payload).hexdigest(), "code_page": code_page})
        return rows

    def hybrid(self):
        require(self.machine == 0xAA64, "the supplied native MFC view is not ARM64")
        config_rva, config_size = unpack_from("<II", self.data, self.optional + 112 + 10 * 8)
        require(config_size >= 0xE8, "MFC load configuration omits dynamic view metadata")
        config = self.offset(config_rva, 0xE8)
        relative, section = unpack_from("<IH", self.data, config + 0xE0)
        require(1 <= section <= len(self.sections), "dynamic view section is absent")
        start = self.sections[section - 1][2] + relative
        version, size = unpack_from("<II", self.data, start)
        require(version == 1, "the MFC dynamic view table is outside the declared version-one scope")
        cursor, stop = start + 8, start + 8 + size
        require(stop <= len(self.data), "the MFC dynamic view table is truncated")
        view, counts, writes = bytearray(self.data), {0: 0, 1: 0, 2: 0}, 0
        while cursor < stop:
            symbol, size = unpack_from("<QI", self.data, cursor)
            cursor += 12
            end = cursor + size
            require(symbol == 6 and end <= stop, "unexpected dynamic relocation family")
            while cursor < end:
                page, block_size = unpack_from("<II", self.data, cursor)
                next_block = cursor + block_size
                require(page % 0x1000 == 0 and block_size >= 8 and block_size % 4 == 0
                        and next_block <= end, "malformed ARM64X relocation block")
                entry = cursor + 8
                while entry < next_block:
                    word = unpack_from("<H", self.data, entry)[0]
                    entry += 2
                    if not word:
                        continue
                    kind, argument = (word >> 12) & 3, word >> 14
                    address = page + (word & 0xFFF)
                    length = 4 if kind == 2 else 1 << argument
                    offset = self.offset(address, length)
                    if kind == 0:
                        data = bytes(length)
                    elif kind == 1:
                        require(argument > 0 and entry + length <= next_block, "truncated ARM64X value")
                        data = self.data[entry:entry + length]
                        entry += length
                    elif kind == 2:
                        require(entry + 2 <= next_block, "truncated ARM64X delta")
                        delta = unpack_from("<H", self.data, entry)[0]
                        entry += 2
                        delta *= (-1 if argument & 1 else 1) * (8 if argument & 2 else 4)
                        number = (int.from_bytes(view[offset:offset + 4], "little") + delta) & 0xFFFFFFFF
                        data = number.to_bytes(4, "little")
                    else:
                        raise ValueError("unknown ARM64X fixup kind")
                    require(address % length == 0, "unaligned ARM64X view field")
                    view[offset:offset + length] = data
                    counts[kind] += 1
                    writes += 1
                require(entry == next_block, "ARM64X entry ended outside its block")
                cursor = next_block
            require(cursor == end, "ARM64X table ended outside its symbol")
        require(cursor == stop, "ARM64X view did not consume its original table")
        image = NativeNamePe(bytes(view))
        require(image.machine == 0x8664, "declared MFC hybrid view is not AMD64-compatible")
        return image, {"original_sha256": self.sha256, "hybrid_sha256": image.sha256,
                       "dynamic_table_version": version, "fixups": writes,
                       "fixup_counts": {str(key): value for key, value in counts.items()},
                       "header_machine_before": hex(self.machine), "header_machine_after": hex(image.machine),
                       "native_execution": False, "binary_written": False}
