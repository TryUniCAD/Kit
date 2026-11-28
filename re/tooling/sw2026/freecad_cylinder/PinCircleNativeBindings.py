from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack_from


RANGES = {
    "make_radial_dimension": (0x4C4CB670, 0x4C4CB882),
    "circle_dimension_constructor": (0x4C40FEC0, 0x4C40FF03),
    "radius_to_diameter": (0x4C42F850, 0x4C42F8C1),
    "diameter_to_radius": (0x4C431170, 0x4C4311E1),
    "dimension_value_getter": (0x4C81FC50, 0x4C81FCC8),
    "dimension_value_setter": (0x4C81FE00, 0x4C820526),
    "length_value_setter": (0x4C19CAE0, 0x4C19CAEF),
    "feature_parameter_auto_name": (0x4BEA1400, 0x4BEA1656),
    "generate_parameter_name": (0x4C820F20, 0x4C820FA8),
    "dimension_parameter_name_setter": (0x4C821C40, 0x4C821D69),
    "sketch_parameter_name_setter": (0x4C430BC0, 0x4C430D81),
    "parameter_name_setter": (0x4C19C9B0, 0x4C19CA17),
    "node_name_storage": (0x4B555250, 0x4B5552DA),
    "secondary_node_flag_setter": (0x4C03ED70, 0x4C03ED7E),
    "node_name_serializer": (0x4C179CA0, 0x4C179CE6),
    "node_lw_serializer": (0x4C17ADF0, 0x4C17B23A),
    "parameter_serializer": (0x4C17A330, 0x4C17A665),
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


class PeImage:
    def __init__(self, path):
        require(path.is_file() and not path.is_symlink(), "use the pinned original regular PE file")
        self.raw = path.read_bytes()
        self.sha256 = sha256(self.raw).hexdigest()
        require(self.sha256 == "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
                "the model module is not the pinned SOLIDWORKS 2026 build")
        pe = unpack_from("<I", self.raw, 0x3C)[0]
        require(self.raw[pe:pe + 4] == b"PE\0\0", "the pinned image has no PE header")
        count = unpack_from("<H", self.raw, pe + 6)[0]
        optional_size = unpack_from("<H", self.raw, pe + 20)[0]
        self.optional = pe + 24
        require(unpack_from("<H", self.raw, self.optional)[0] == 0x20B, "the image is not PE32+")
        self.base = unpack_from("<Q", self.raw, self.optional + 24)[0]
        self.sections = []
        for index in range(count):
            offset = self.optional + optional_size + index * 40
            _, start, size, raw = unpack_from("<IIII", self.raw, offset + 8)
            self.sections.append((start, size, raw))

    def offset(self, address, size=1):
        relative = address - self.base
        for start, length, raw in self.sections:
            if start <= relative and relative + size <= start + length:
                return raw + relative - start
        raise ValueError("the requested native address is not backed by the pinned PE file")

    def value(self, format_value, address):
        return unpack_from(format_value, self.raw, self.offset(address))[0]

    def wide(self, address):
        values = []
        for index in range(64):
            character = self.value("<H", address + index * 2)
            if character == 0:
                return b"".join(value.to_bytes(2, "little") for value in values).decode("utf-16-le")
            values.append(character)
        raise ValueError("the selected format-vocabulary string has no bounded terminator")

    def ascii(self, relative):
        start = self.offset(self.base + relative)
        end = self.raw.index(b"\0", start)
        return self.raw[start:end].decode("ascii")

    def imports(self):
        directory = unpack_from("<I", self.raw, self.optional + 112 + 8)[0]
        selected = {}
        ordinal = 0
        wanted = {0x4CD3DA28, 0x4CD3DA30, 0x4CD3D870, 0x4CD3D878, 0x4CD352A0}
        while True:
            offset = self.offset(self.base + directory) + ordinal * 20
            original, stamp, chain, name, first = unpack_from("<IIIII", self.raw, offset)
            ordinal += 1
            if not any((original, stamp, chain, name, first)):
                break
            dll = self.ascii(name)
            index = 0
            while True:
                address = self.base + (original or first) + index * 8
                value = self.value("<Q", address)
                if value == 0:
                    break
                slot = self.base + first + index * 8
                if slot in wanted:
                    selected[hex(slot)] = {"module": dll, "symbol": "#" + str(value & 0xFFFF)
                                           if value >> 63 else self.ascii(value + 2)}
                index += 1
        require(set(selected) == {hex(value) for value in wanted}, "the expected imported archive ownership differs")
        return selected

    def window(self, low, high):
        offset = self.offset(low, high - low)
        raw = self.raw[offset:offset + high - low]
        return {"start": hex(low), "end": hex(high), "rva": hex(low - self.base),
                "file_offset": offset, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def inspect(image):
    circle_table = 0x4CF79588
    slots = {"value_getter": 0x88, "parameter_getter": 0xA0, "value_setter": 0x1B8,
             "generate_name": 0x1E0, "set_parameter_name": 0x220}
    targets = {name: hex(image.value("<Q", circle_table + offset)) for name, offset in slots.items()}
    require(targets == {"value_getter": "0x4c81fc50", "parameter_getter": "0x4b284b80",
                        "value_setter": "0x4c81fe00", "generate_name": "0x4c820f20",
                        "set_parameter_name": "0x4c430bc0"}, "the actual circle virtual owners changed")
    prefix_address = image.value("<Q", 0x4DB03700)
    prefix, format_value = image.wide(prefix_address), image.wide(0x4CDF9D88)
    factors = {"radius_to_diameter": image.value("<d", 0x4CD9E318),
               "diameter_to_radius": image.value("<d", 0x4CD9A3C0)}
    require(factors == {"radius_to_diameter": 2.0, "diameter_to_radius": 0.5}
            and prefix == "D" and format_value == "%s%d", "the pinned conversion or naming vocabulary differs")
    name_serializer = image.value("<Q", 0x4CD8CE98 + 5 * 8)
    require(name_serializer == 0x4C179CA0, "the actual node-name serializer differs")
    return {
        "schema": "kit.sw2026.circle-native-parameter-bindings.v1", "passed": True,
        "image": {"sha256": image.sha256, "bytes": len(image.raw), "base": hex(image.base), "format": "pe32-plus"},
        "methods": {name: image.window(*extent) for name, extent in RANGES.items()},
        "circle_virtuals": {"table": hex(circle_table), "slots": {name: hex(value) for name, value in slots.items()},
                            "targets": targets},
        "mode_factors": factors,
        "automatic_name": {"prefix_pointer": "0x4db03700", "prefix_address": hex(prefix_address),
                           "prefix": prefix, "format_address": "0x4cdf9d88", "format": format_value},
        "node_name_serializer": {"vtable": "0x4cd8ce98", "vendor_slot": 5, "target": hex(name_serializer)},
        "imports": image.imports(),
        "target_execution": False, "native_processes_started": 0, "heldout_inputs_read": 0,
        "generated_native_files": 0, "custom_name_native_acceptance": False,
        "scope": "static exact-build bindings only; method semantics are independently recorded",
    }


def main():
    parser = ArgumentParser(description="Pin static circle mode and parameter-name ownership without executing vendor code")
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = inspect(PeImage(args.image))
    raw = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"passed": True, "output_sha256": sha256(raw).hexdigest(), "method_ranges": len(RANGES),
                      "native_processes_started": 0, "heldout_inputs_read": 0}))


if __name__ == "__main__":
    main()
