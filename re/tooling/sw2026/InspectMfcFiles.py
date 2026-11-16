from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import struct


PINNED_EXECUTABLE_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
EXPECTED_EXECUTABLE_VERSION = (34, 5, 2, 604)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def reparse(path):
    value = path.lstat()
    return stat.S_ISLNK(value.st_mode) or bool(getattr(value, "st_file_attributes", 0) & 0x400)


def check_chain(path):
    for parent in (path, *path.parents):
        if os.path.lexists(parent) and reparse(parent):
            raise ValueError(f"reparse point is outside discovery scope: {parent}")


def inside_checkout(path):
    return any((parent / ".git").exists() for parent in (path, *path.parents))


def write_json(path, value):
    pending = path.with_suffix(".pending.json")
    with pending.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    pending.replace(path)


class PeFile:
    def __init__(self, stream, size):
        self.stream, self.size = stream, size
        if self.read(0, 2) != b"MZ":
            raise ValueError("missing DOS signature")
        pe = struct.unpack("<I", self.read(0x3C, 4))[0]
        if self.read(pe, 4) != b"PE\0\0":
            raise ValueError("missing PE signature")
        coff = struct.unpack("<HHIIIHH", self.read(pe + 4, 20))
        self.machine, section_count, self.timestamp = coff[:3]
        optional_size = coff[5]
        optional = self.read(pe + 24, optional_size)
        if len(optional) < 64:
            raise ValueError("short optional header")
        self.magic = struct.unpack_from("<H", optional)[0]
        if self.magic == 0x20B:
            count_offset, directory_offset = 108, 112
        elif self.magic == 0x10B:
            count_offset, directory_offset = 92, 96
        else:
            raise ValueError(f"unsupported optional header: {self.magic:#x}")
        if len(optional) < count_offset + 4:
            raise ValueError("short data-directory count")
        self.header_size = struct.unpack_from("<I", optional, 60)[0]
        directory_count = struct.unpack_from("<I", optional, count_offset)[0]
        self.export_rva, self.export_size = 0, 0
        self.resource_rva, self.resource_size = 0, 0
        if directory_count:
            if len(optional) < directory_offset + 8:
                raise ValueError("short export directory entry")
            self.export_rva, self.export_size = struct.unpack_from("<II", optional, directory_offset)
        if directory_count > 2:
            if len(optional) < directory_offset + 24:
                raise ValueError("short resource directory entry")
            self.resource_rva, self.resource_size = struct.unpack_from("<II", optional, directory_offset + 16)
        self.sections = []
        start = pe + 24 + optional_size
        table = self.read(start, section_count * 40)
        for index in range(section_count):
            name, virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<8sIIII", table, index * 40)
            characteristics = struct.unpack_from("<I", table, index * 40 + 36)[0]
            self.sections.append({
                "name": name.rstrip(b"\0").decode("ascii", errors="backslashreplace"),
                "virtual_size": virtual_size,
                "rva": rva,
                "raw_size": raw_size,
                "raw_offset": raw_offset,
                "characteristics": characteristics,
            })

    def read(self, offset, length):
        if offset < 0 or length < 0 or offset + length > self.size:
            raise ValueError("PE read exceeds file bounds")
        self.stream.seek(offset)
        value = self.stream.read(length)
        if len(value) != length:
            raise ValueError("short PE read")
        return value

    def locate(self, rva, length):
        if 0 <= rva < self.header_size and rva + length <= self.header_size:
            return rva, self.header_size - rva, None
        for section in self.sections:
            delta = rva - section["rva"]
            if 0 <= delta < max(section["virtual_size"], section["raw_size"]):
                if delta + length > section["raw_size"]:
                    raise ValueError("RVA has no complete file-backed range")
                return section["raw_offset"] + delta, section["raw_size"] - delta, section
        raise ValueError(f"unmapped RVA: {rva:#x}")

    def read_rva(self, rva, length):
        offset, available, section = self.locate(rva, length)
        return self.read(offset, length)

    def text(self, rva):
        offset, available, section = self.locate(rva, 1)
        value = self.read(offset, min(available, 4096, self.size - offset))
        end = value.find(b"\0")
        if end < 0:
            raise ValueError("unterminated or over-limit export string")
        return value[:end].decode("ascii")

    def exports(self):
        if not self.export_rva or not self.export_size:
            return {"present": False, "ordinals": []}
        if self.export_size < 40:
            raise ValueError("short export directory")
        fields = struct.unpack("<IIHHIIIIIII", self.read_rva(self.export_rva, 40))
        flags, timestamp, major, minor, name, base, functions, names, addresses, name_rvas, indices = fields
        requested = {ordinal - base: ordinal for ordinal in (12087, 14278) if 0 <= ordinal - base < functions}
        aliases = {index: [] for index in requested}
        ordinal_table = self.read_rva(indices, names * 2) if names else b""
        name_table = self.read_rva(name_rvas, names * 4) if names else b""
        for index in range(names):
            target = struct.unpack_from("<H", ordinal_table, index * 2)[0]
            if target >= functions:
                raise ValueError("export name ordinal exceeds address table")
            if target in aliases:
                aliases[target].append(self.text(struct.unpack_from("<I", name_table, index * 4)[0]))
        records = []
        for ordinal in (12087, 14278):
            index = ordinal - base
            item = {"ordinal": ordinal, "address_table_index": index, "names": aliases.get(index, [])}
            if index not in requested:
                item["status"] = "outside_address_table"
            else:
                rva = struct.unpack("<I", self.read_rva(addresses + index * 4, 4))[0]
                item["rva"] = rva
                if rva == 0:
                    item["status"] = "unassigned"
                elif self.export_rva <= rva < self.export_rva + self.export_size:
                    item.update(status="forwarded", forwarder=self.text(rva))
                else:
                    offset, available, section = self.locate(rva, 1)
                    item.update(
                        status="file_backed_export",
                        file_offset=offset,
                        section=None if section is None else section["name"],
                        section_executable=False if section is None else bool(section["characteristics"] & 0x20000000),
                    )
            records.append(item)
        return {
            "present": True,
            "dll_name": self.text(name),
            "directory_rva": self.export_rva,
            "directory_size": self.export_size,
            "timestamp_raw": timestamp,
            "version_major": major,
            "version_minor": minor,
            "ordinal_base": base,
            "address_count": functions,
            "name_count": names,
            "ordinals": records,
        }

    def resource(self, offset, length):
        if offset < 0 or length < 0 or offset + length > self.resource_size:
            raise ValueError("resource read exceeds directory bounds")
        return self.read_rva(self.resource_rva + offset, length)

    def resource_entries(self, offset):
        header = struct.unpack("<IIHHHH", self.resource(offset, 16))
        count = header[4] + header[5]
        table = self.resource(offset + 16, count * 8)
        return [struct.unpack_from("<II", table, index * 8) for index in range(count)]

    def resource_name(self, value):
        if not value & 0x80000000:
            return value
        offset = value & 0x7FFFFFFF
        length = struct.unpack("<H", self.resource(offset, 2))[0]
        return self.resource(offset + 2, length * 2).decode("utf-16-le")

    def version_value(self, payload):
        if len(payload) < 6:
            raise ValueError("short version-resource block")
        length, value_length, value_type = struct.unpack_from("<HHH", payload)
        if length < 6 or length > len(payload) or value_type != 0 or value_length != 52:
            raise ValueError("unsupported VS_VERSION_INFO framing")
        end = 6
        while end + 2 <= length and payload[end:end + 2] != b"\0\0":
            end += 2
        if end + 2 > length or payload[6:end].decode("utf-16-le") != "VS_VERSION_INFO":
            raise ValueError("invalid VS_VERSION_INFO key")
        start = (end + 2 + 3) & ~3
        if start + value_length > length:
            raise ValueError("short VS_FIXEDFILEINFO value")
        words = struct.unpack_from("<13I", payload, start)
        if words[0] != 0xFEEF04BD:
            raise ValueError("invalid VS_FIXEDFILEINFO signature")
        names = (
            "signature", "structure_version", "file_version_ms", "file_version_ls",
            "product_version_ms", "product_version_ls", "file_flags_mask", "file_flags",
            "file_os", "file_type", "file_subtype", "file_date_ms", "file_date_ls",
        )
        fixed = dict(zip(names, words, strict=True))
        for prefix, high, low in (("file", words[2], words[3]), ("product", words[4], words[5])):
            parts = [high >> 16, high & 0xFFFF, low >> 16, low & 0xFFFF]
            fixed[f"{prefix}_version_words"] = parts
            fixed[f"{prefix}_version"] = ".".join(str(part) for part in parts)
            fixed[f"{prefix}_version_build_padded"] = f"{parts[0]}.{parts[1]}.{parts[2]}.{parts[3]:04d}"
        return fixed

    def versions(self):
        result = {
            "directory_rva": self.resource_rva,
            "directory_size": self.resource_size,
            "version_type_present": False,
            "entries": [],
        }
        if not self.resource_rva or not self.resource_size:
            return result

        def visit(offset, path, ancestors):
            if offset in ancestors or len(path) > 3:
                raise ValueError("cyclic or over-depth version-resource tree")
            ancestors = ancestors | {offset}
            for name, target in self.resource_entries(offset):
                branch = [*path, self.resource_name(name)]
                if target & 0x80000000:
                    visit(target & 0x7FFFFFFF, branch, ancestors)
                    continue
                if len(branch) != 3:
                    raise ValueError("unsupported version-resource tree shape")
                rva, size, code_page, reserved = struct.unpack("<IIII", self.resource(target, 16))
                payload = self.resource(rva - self.resource_rva, size)
                result["entries"].append({
                    "path": branch,
                    "data_rva": rva,
                    "bytes": size,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "code_page": code_page,
                    "reserved": reserved,
                    "fixed_info": self.version_value(payload),
                })

        for name, target in self.resource_entries(0):
            if name != 16:
                continue
            result["version_type_present"] = True
            if not target & 0x80000000:
                raise ValueError("version-resource type has no directory")
            visit(target & 0x7FFFFFFF, [16], {0})
        return result


def inspect_file(path, include_exports=True):
    check_chain(path)
    if inside_checkout(path):
        raise ValueError("licensed input is inside a repository checkout")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("input is not a regular file")
        digest = hashlib.sha256()
        while block := stream.read(1024 * 1024):
            digest.update(block)
        result = {
            "path": str(path),
            "bytes": before.st_size,
            "sha256": digest.hexdigest(),
            "mtime_ns": before.st_mtime_ns,
            "file_identity": {"device": before.st_dev, "inode": before.st_ino},
            "inspected_at": utc_now(),
        }
        try:
            pe = PeFile(stream, before.st_size)
            result["pe"] = {
                "machine": pe.machine,
                "machine_hex": f"0x{pe.machine:04x}",
                "machine_is_amd64": pe.machine == 0x8664,
                "optional_header_magic": pe.magic,
                "coff_timestamp_raw": pe.timestamp,
            }
            if include_exports:
                result["pe"]["exports"] = pe.exports()
            result["pe"]["version_resources"] = pe.versions()
        except (ValueError, UnicodeError, struct.error) as error:
            result["metadata_error"] = f"{type(error).__name__}: {error}"
        after = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("input changed during hashing or metadata reads")
    return result


def scan_root(root, files, errors, skipped):
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            if reparse(directory):
                skipped.append({"path": str(directory), "reason": "directory_became_reparse_point"})
                continue
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    try:
                        info = entry.stat(follow_symlinks=False)
                        if stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400):
                            skipped.append({"path": str(path), "reason": "reparse_point"})
                        elif stat.S_ISDIR(info.st_mode):
                            pending.append(path)
                        elif entry.name.casefold() == "mfc140u.dll":
                            files.append(path)
                    except OSError as error:
                        errors.append({"path": str(path), "error": f"{type(error).__name__}: {error}"})
        except OSError as error:
            errors.append({"path": str(directory), "error": f"{type(error).__name__}: {error}"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--solidworks-root", action="append", type=Path)
    parser.add_argument("--source-revision")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("this tool is limited to filesystem discovery in the Windows guest")
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    program_files = list(dict.fromkeys(Path(os.environ[key]) for key in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)") if os.environ.get(key)))
    if not program_files:
        parser.error("Program Files directory identities are unavailable")
    solidworks = args.solidworks_root or [program_files[0] / "SOLIDWORKS Corp" / "SOLIDWORKS"]
    roots = [(root, "solidworks_install") for root in solidworks]
    roots.append((windows / "WinSxS", "windows_component_store"))
    for root in program_files:
        roots.extend(((root / "Common Files" / "Microsoft Shared", "microsoft_shared"), (root / "Microsoft Visual Studio", "visual_studio")))
    explicit_files = [windows / "System32" / "mfc140u.dll", windows / "SysWOW64" / "mfc140u.dll"]
    output = args.output
    try:
        if not output.is_absolute() or not output.parent.is_dir() or os.path.lexists(output):
            raise ValueError("output must be a new absolute directory with an existing parent")
        check_chain(output)
        output = output.resolve()
        if inside_checkout(output):
            raise ValueError("output must be outside repository checkouts")
        for root in (windows, *program_files, *solidworks):
            if not root.is_absolute():
                raise ValueError(f"discovery root must be absolute: {root}")
            if output.is_relative_to(root.resolve()):
                raise ValueError("output must be outside Windows and installation roots")
        if args.source_revision is not None and (len(args.source_revision) != 40 or any(value not in "0123456789abcdefABCDEF" for value in args.source_revision)):
            raise ValueError("source revision must be a complete hexadecimal commit identity")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    output.mkdir()
    record = {
        "schema": "kit.solidworks.mfc-file-inventory.v1",
        "started_at": utc_now(),
        "state": "running",
        "stage": "enumeration",
        "argv": sys.argv,
        "python": sys.version,
        "python_executable": sys.executable,
        "python_orig_argv": getattr(sys, "orig_argv", None),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_revision": args.source_revision,
        "native_implementation_bound": False,
        "acceptance": False,
        "roots": [],
        "explicit_files": [{"path": str(path), "status": "pending"} for path in explicit_files],
        "files": [],
        "errors": [],
        "skipped": [],
    }
    write_json(output / "Record.json", record)
    discovered, seen = [], set()
    for root, kind in roots:
        if str(root).casefold() in seen:
            continue
        seen.add(str(root).casefold())
        item = {"path": str(root), "kind": kind, "started_at": utc_now()}
        record["roots"].append(item)
        try:
            check_chain(root)
            if inside_checkout(root):
                raise ValueError("licensed discovery root is inside a repository checkout")
            try:
                info = root.lstat()
            except FileNotFoundError:
                item["status"] = "absent"
            else:
                if not stat.S_ISDIR(info.st_mode):
                    raise ValueError("discovery root is not a directory")
                if kind == "solidworks_install":
                    witness_path = root / "SLDWORKS.exe"
                    check_chain(witness_path)
                    if not witness_path.is_file():
                        raise ValueError("explicit SOLIDWORKS root has no SLDWORKS.exe witness")
                    witness = inspect_file(witness_path, include_exports=False)
                    versions = witness.get("pe", {}).get("version_resources", {}).get("entries", [])
                    version_match = all(tuple(entry["fixed_info"]["file_version_words"]) == EXPECTED_EXECUTABLE_VERSION for entry in versions) if versions else None
                    witness.update({
                        "expected_sha256": PINNED_EXECUTABLE_SHA256,
                        "expected_file_version_words": list(EXPECTED_EXECUTABLE_VERSION),
                        "expected_file_version": "34.5.2.0604",
                        "sha256_matches_expected": witness["sha256"] == PINNED_EXECUTABLE_SHA256,
                        "observed_file_version_matches_expected": version_match,
                        "verified_pinned_executable": witness["sha256"] == PINNED_EXECUTABLE_SHA256 and version_match is True and "metadata_error" not in witness,
                    })
                    item["executable_witness"] = witness
                    if "metadata_error" in witness:
                        record["errors"].append({"path": str(witness_path), "error": witness["metadata_error"]})
                item["status"] = "enumerated"
                scan_root(root, discovered, record["errors"], record["skipped"])
        except (OSError, ValueError) as error:
            item["status"] = "rejected"
            record["errors"].append({"path": str(root), "error": f"{type(error).__name__}: {error}"})
        item["finished_at"] = utc_now()
        write_json(output / "Record.json", record)
    for path, item in zip(explicit_files, record["explicit_files"], strict=True):
        try:
            path.lstat()
            item["status"] = "present"
            discovered.append(path)
        except FileNotFoundError:
            item["status"] = "absent"
        except OSError as error:
            item["status"] = "unavailable"
            record["errors"].append({"path": str(path), "error": f"{type(error).__name__}: {error}"})
    record["stage"] = "file_metadata"
    for path in sorted(set(discovered), key=lambda value: str(value).casefold()):
        try:
            item = inspect_file(path)
            record["files"].append(item)
            if "metadata_error" in item:
                record["errors"].append({"path": str(path), "error": item["metadata_error"]})
        except (OSError, ValueError) as error:
            record["errors"].append({"path": str(path), "error": f"{type(error).__name__}: {error}"})
        write_json(output / "Record.json", record)
    record.update(
        state="completed",
        stage="finished",
        finished_at=utc_now(),
        scan_complete=not record["errors"] and not record["skipped"],
        file_count=len(record["files"]),
    )
    write_json(output / "Inventory.json", record)
    write_json(output / "Record.json", record)
    print(json.dumps({"output": str(output), "files": len(record["files"]), "scan_complete": record["scan_complete"], "native_implementation_bound": False}))
    return 0 if record["scan_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
