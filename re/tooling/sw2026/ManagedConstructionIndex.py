import argparse
import hashlib
import importlib.metadata
import json
import struct
from pathlib import Path

import dnfile
import pefile
from dncil.cil.body import CilMethodBody
from dncil.cil.body.reader import CilMethodBodyReaderBytes


PARSER_VERSIONS = {"dnfile": "0.18.0", "dncil": "1.0.2", "pefile": "2024.8.26"}
FAMILY_NAMES = {
    "extrude": ("extrud", "extrus"),
    "revolve": ("revolv", "revolut"),
    "fillet": ("fillet",),
    "shell": ("shell",),
    "hole": ("hole",),
    "sweep": ("sweep",),
    "loft": ("loft",),
    "pattern": ("pattern",),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def type_name(row):
    return ".".join(
        value for value in (str(row.TypeNamespace), str(row.TypeName)) if value
    )


def module_identity(path, image):
    return {
        "name": path.name,
        "bytes": path.stat().st_size,
        "sha256": digest(path.read_bytes()),
        "image_base": hex(image.OPTIONAL_HEADER.ImageBase),
        "machine": hex(image.FILE_HEADER.Machine),
    }


class ManagedIndex:
    def __init__(self, path, expected_sha256, native_path, native_sha256):
        self.path = Path(path).resolve(strict=True)
        if digest(self.path.read_bytes()) != expected_sha256:
            raise ValueError("Managed module identity mismatch")
        self.image = dnfile.dnPE(str(self.path), clr_lazy_load=True)
        if self.image.net is None:
            raise ValueError("The declared module has no CLI metadata")
        self.methods = {}
        self.fields = {}
        self.native = None
        self.native_exports = {}
        for row in self.image.net.mdtables.TypeDef.rows:
            name = type_name(row)
            for method in row.MethodList:
                self.methods[method.row_index] = name
            for field in row.FieldList:
                self.fields[field.row_index] = name
        self.imports = {
            entry.address: {
                "module": library.dll.decode("ascii"),
                "symbol": entry.name.decode("ascii") if entry.name else None,
                "ordinal": entry.ordinal,
            }
            for library in self.image.DIRECTORY_ENTRY_IMPORT
            for entry in library.imports
        }
        if native_path is not None:
            native_path = Path(native_path).resolve(strict=True)
            if digest(native_path.read_bytes()) != native_sha256:
                raise ValueError("Native module identity mismatch")
            self.native = pefile.PE(str(native_path))
            self.native_identity = module_identity(native_path, self.native)
            self.native_exports = {
                entry.name.decode("ascii"): entry
                for entry in self.native.DIRECTORY_ENTRY_EXPORT.symbols
                if entry.name
            }

    def token(self, value):
        table_id, ordinal = value >> 24, value & 0xFFFFFF
        table_names = {
            1: "TypeRef",
            2: "TypeDef",
            4: "Field",
            6: "MethodDef",
            10: "MemberRef",
            17: "StandAloneSig",
            27: "TypeSpec",
        }
        name = table_names.get(table_id)
        result = {"token": f"0x{value:08x}", "table": name or hex(table_id)}
        table = getattr(self.image.net.mdtables, name, None) if name else None
        if table is None or not 0 < ordinal <= len(table.rows):
            return result
        row = table.rows[ordinal - 1]
        if hasattr(row, "Name"):
            result["name"] = str(row.Name)
        if table_id in (1, 2):
            result["name"] = type_name(row)
        elif table_id == 6:
            result["owner"] = self.methods[ordinal]
            result["rva"] = hex(row.Rva)
        elif table_id == 4:
            result["owner"] = self.fields[ordinal]
        elif table_id == 10:
            parent = row.Class
            if parent.table.name in ("TypeRef", "TypeDef"):
                result["owner"] = type_name(parent.row)
        return result

    def native_boundary(self, row):
        code = self.image.get_data(row.Rva, 6)
        if code[:2] != b"\xff\x25":
            return {"kind": "native-body-unmapped", "body_read": False}
        address = self.image.OPTIONAL_HEADER.ImageBase + row.Rva
        iat = address + 6 + struct.unpack("<i", code[2:])[0]
        target = self.imports.get(iat)
        if target is None:
            raise ValueError("Native indirect jump has no declared import")
        result = {
            "kind": "native-import-thunk",
            "thunk_bytes": 6,
            "thunk_sha256": digest(code),
            "iat_rva": hex(iat - self.image.OPTIONAL_HEADER.ImageBase),
            **target,
        }
        if self.native is not None:
            matching = target["module"].lower() == self.native_identity["name"].lower()
            export = self.native_exports.get(target["symbol"]) if matching else None
            if export is not None and export.forwarder is None:
                result["target_rva"] = hex(export.address)
                result["target_address"] = hex(
                    self.native.OPTIONAL_HEADER.ImageBase + export.address
                )
                result["target_module_sha256"] = self.native_identity["sha256"]
        return result

    def method(self, token):
        if token >> 24 != 6 or not 0 < token & 0xFFFFFF <= len(self.methods):
            raise ValueError("An explicit MethodDef token is required")
        row = self.image.net.mdtables.MethodDef.rows[(token & 0xFFFFFF) - 1]
        result = {
            **self.token(token),
            "implementation_flags": hex(row.struct.ImplFlags),
            "method_flags": hex(row.struct.Flags),
            "signature_sha256": digest(row.Signature.value),
            "managed": row.ImplFlags.miManaged,
            "cil": row.ImplFlags.miIL,
            "native": row.ImplFlags.miNative,
            "abstract": row.Flags.mdAbstract,
        }
        if not row.Rva:
            result["body_kind"] = "absent-rva"
        elif row.ImplFlags.miNative:
            result["body_kind"] = "native"
            result["boundary"] = self.native_boundary(row)
        elif row.ImplFlags.miIL:
            body = CilMethodBody(
                CilMethodBodyReaderBytes(self.image.get_data(row.Rva, 1 << 20))
            )
            raw = body.get_bytes()
            result.update(
                {
                    "body_kind": "cil",
                    "header_bytes": body.header_size,
                    "code_bytes": body.code_size,
                    "complete_body_bytes": body.size,
                    "code_sha256": digest(
                        raw[body.header_size : body.header_size + body.code_size]
                    ),
                    "complete_body_sha256": digest(raw),
                    "instruction_count": len(body.instructions),
                    "exception_region_count": len(body.exception_handlers),
                    "call_edges": [],
                }
            )
            edges = {}
            for instruction in body.instructions:
                if instruction.opcode.name not in ("call", "callvirt", "newobj", "ldftn", "calli"):
                    continue
                target = self.token(instruction.operand.value)
                key = (instruction.opcode.name, instruction.operand.value)
                if key not in edges:
                    edges[key] = {
                        "cil_code_offsets": [],
                        "dispatch": instruction.opcode.name,
                        "target": target,
                        "resolution": "metadata-declaration",
                    }
                edges[key]["cil_code_offsets"].append(instruction.offset - body.header_size)
            result["call_edges"] = list(edges.values())
        else:
            result["body_kind"] = "unmapped-implementation"
        return result

    def family_index(self):
        result = {family: [] for family in FAMILY_NAMES}
        for ordinal, row in enumerate(self.image.net.mdtables.TypeDef.rows, 1):
            name = type_name(row)
            if not any(marker in name for marker in ("Request", "Packet", "Evaluator")):
                continue
            for family, matches in FAMILY_NAMES.items():
                if any(match in name.lower() for match in matches):
                    result[family].append(
                        {
                            "token": f"0x{0x02000000 | ordinal:08x}",
                            "name": name,
                            "method_count": len(row.MethodList),
                            "method_bodies_decoded": 0,
                        }
                    )
        return result

    def receipt(self, tokens, family_index):
        module = self.image.net.mdtables.Module.rows[0]
        result = {
            "schema": "kit.sw2026.managed-construction-index.v1",
            "tool_sha256": digest(Path(__file__).read_bytes()),
            "module": {
                **module_identity(self.path, self.image),
                "mvid": str(module.Mvid),
                "cli_flags": hex(self.image.net.struct.Flags),
                "metadata_version": self.image.net.metadata.struct.Version.rstrip(b"\x00").decode("ascii"),
                "type_count": len(self.image.net.mdtables.TypeDef.rows),
                "method_count": len(self.image.net.mdtables.MethodDef.rows),
            },
            "parser_versions": PARSER_VERSIONS,
            "query": {"method_tokens": [f"0x{token:08x}" for token in tokens], "family_index": family_index},
            "methods": [self.method(token) for token in tokens],
            "limits": {
                "target_executed": False,
                "runtime_dispatch_verified": False,
                "vendor_code_or_bodies_emitted": False,
                "native_body_decoded_as_cil": False,
                "unselected_method_bodies_decoded": 0,
                "writer_output_count": 0,
            },
        }
        if self.native is not None:
            result["native_module"] = self.native_identity
        if family_index:
            result["adjacent_request_types"] = self.family_index()
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("module", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--native-module", type=Path)
    parser.add_argument("--native-sha256")
    parser.add_argument("--method", action="append", default=[])
    parser.add_argument("--family-index", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if bool(args.native_module) != bool(args.native_sha256):
        parser.error("Native module path and digest must be supplied together")
    observed = {name: importlib.metadata.version(name) for name in PARSER_VERSIONS}
    if observed != PARSER_VERSIONS:
        raise ValueError(f"Parser versions differ: {observed}")
    tokens = [int(token, 16) for token in args.method]
    if len(set(tokens)) != len(tokens):
        parser.error("Duplicate method tokens")
    image = ManagedIndex(args.module, args.expected_sha256, args.native_module, args.native_sha256)
    result = image.receipt(tokens, args.family_index)
    encoded = (json.dumps(result, indent=2) + "\n").encode("utf-8")
    if args.check:
        if args.output.read_bytes() != encoded:
            raise ValueError("The pinned metadata receipt differs")
    else:
        args.output.write_bytes(encoded)
    print(json.dumps({"sha256": digest(encoded), "methods": len(tokens), "code_emitted": False, "checked": args.check}))


if __name__ == "__main__":
    main()
