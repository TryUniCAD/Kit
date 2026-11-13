"""Same-length scrubber for account residue inside Fusion-saved archives.

Fusion copies uninitialized heap bytes into protein asset members, and those
bytes can hold account identifiers, home paths and cloud document ids. Every
rule here is generic: it keys on JSON field names, path shapes and URN
prefixes, never on a particular account. Replacements keep byte lengths so
length prefixes and offsets inside members stay valid. Unchanged members are
copied byte for byte; changed members are recompressed with their original
method, and every header field other than CRC, sizes and offsets is kept.

Usage: python3.14 ScrubSaved.py [--dry-run] [--ledger PATH] ARCHIVE...
All archives in one run share one placeholder map, so a cloud id that appears
in several archives receives the same placeholder in each of them.
"""

import argparse
import hashlib
import hmac
import io
import json
import re
import secrets
import struct
import sys
import zipfile
import zlib
from compression import zstd
from pathlib import Path

ACCOUNT_KEYS = (
    "hubId",
    "hubIdHashed",
    "spaceCollectionId",
    "hubEdition",
    "user_id",
    "userId",
    "ownerId",
    "oxygenId",
    "fileId",
    "teamProjectID",
    "lineageHash",
    "user_hub_urn",
    "session_id",
)
NAME_KEYS = (
    "ownerName",
    "userName",
    "user_name",
    "displayUserName",
    "createUserName",
    "lastModifiedUserName",
    "lastUpdateUserName",
    "creatorName",
    "authorName",
    "fullName",
    "firstName",
    "lastName",
)
RULES = ("account", "name", "home", "urn", "echo")
MIN_KEY_TAIL = 4
MIN_LEARNED = 6
MIN_FRAGMENT = 7
MIN_HEX_FRAGMENT = 10
MAX_DEPTH = 4
LOCAL = struct.Struct("<4sHHHHHLLLHH")
CENTRAL = struct.Struct("<4sHHHHHHLLLHHHHHLL")
END = struct.Struct("<4sHHHHLLH")
LOCAL_SIG = b"PK\x03\x04"
CENTRAL_SIG = b"PK\x01\x02"
END_SIG = b"PK\x05\x06"
DESCRIPTOR_SIG = b"PK\x07\x08"
DEFLATE_LEVELS = {0: 6, 2: 9, 4: 2, 6: 1}
HOME_PLACEHOLDER = b"user"
REASON = "Fusion copies uninitialized heap bytes with account identifiers, home paths and cloud ids into saved archives, so these fixtures were rewritten with same-length placeholders before publication."


def key_tails(keys):
    tails = {key[start:] for key in keys if key.lower().endswith("id") for start in range(1, len(key) - MIN_KEY_TAIL + 1)}
    return b"|".join(re.escape(tail.encode()) for tail in sorted(tails, key=lambda tail: (-len(tail), tail)))


def alternation(keys):
    return b"|".join(re.escape(key.encode()) for key in sorted(keys, key=lambda key: (-len(key), key)))


def wide(pattern):
    return b"".join(re.escape(bytes([byte])) + b"\x00" for byte in pattern)


ACCOUNT = re.compile(rb"(?:" + alternation(ACCOUNT_KEYS) + rb')"\s*:\s*("?)([A-Za-z0-9_.+/=-]+)')
ACCOUNT_TAIL = re.compile(rb"(?:" + key_tails(ACCOUNT_KEYS) + rb')"\s*:\s*("?)([A-Za-z0-9_.+/=-]*[0-9][A-Za-z0-9_.+/=-]*)')
NAMED = re.compile(rb"(?:" + alternation(NAME_KEYS) + rb')"\s*:\s*"([^"\x00-\x1f]{1,80})')
OWNER = b'","ownerId"'
LINK = (b"?show=", b"?version=")
NAME_BYTES = re.compile(rb'[^"\x00-\x1f]')
LINK_BYTES = re.compile(rb"[A-Za-z0-9_=-]")
LITERALS = (b"true", b"false", b"null")
HOME = re.compile(rb"[\\/]{1,2}Users[\\/]{1,2}([A-Za-z0-9._-]+)")
HOME_WIDE = re.compile(rb"(?:[\\/]\x00){1,2}" + wide(b"Users") + rb"(?:[\\/]\x00){1,2}((?:[A-Za-z0-9._-]\x00)+)")
URN_PREFIX = rb"(?:dm\.(?:lineage|folder|version):|fs\.(?:file|folder):[a-z]{2}\.|wip\.dm\.[a-z]+:|prod\.project:|lineage:|versionedFile:)"
URN = re.compile(URN_PREFIX + rb"([A-Za-z0-9_-]{6,})")
URN_WIDE = re.compile(
    rb"(?:"
    + b"|".join(
        wide(prefix)
        for prefix in (b"dm.lineage:", b"dm.folder:", b"dm.version:", b"fs.file:vf.", b"fs.folder:co.", b"prod.project:", b"lineage:", b"versionedFile:")
    )
    + rb")((?:[A-Za-z0-9_-]\x00){6,})"
)
HUB = re.compile(rb"(?<![A-Za-z0-9])a\.((?:YnVzaW5lc3M|cGVyc29uYWw|cHJvamVjd)[A-Za-z0-9_=-]*)")
PROJECT = re.compile(rb"(?<![A-Za-z0-9])b\.([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
SYNTHETIC = re.compile(rb"(?:Kit|Synthetic)[A-Za-z]*[0-9]*")
SHARED = (b"Shared", HOME_PLACEHOLDER)


def keep(value):
    return SYNTHETIC.fullmatch(value) is not None or value in LITERALS


def backward(blob, marker, allowed, limit, minimum):
    found = []
    start = blob.find(marker)
    while start >= 0:
        cursor = start
        while cursor > 0 and start - cursor < limit and allowed.fullmatch(blob[cursor - 1 : cursor]):
            cursor -= 1
        if start - cursor >= minimum:
            found.append((cursor, start))
        start = blob.find(marker, start + 1)
    return found


class Masker:
    def __init__(self, key):
        self.key = key
        self.learned = set()
        self.cache = {}
        self.echo = None
        self.anchors = {}

    def learn(self, value, minimum=MIN_LEARNED):
        if len(value) >= minimum and not keep(value):
            self.learned.add(value)

    def seal(self):
        values = sorted(self.learned, key=lambda value: (-len(value), value))
        kept = []
        for value in values:
            if not any(value != other and (other.startswith(value) or other.endswith(value)) for other in kept):
                kept.append(value)
        self.learned = kept
        anchors = {}
        for value in kept:
            mask = self.fresh(value)
            for form, cover, step in ((value, mask, 1), (value.decode("latin-1").encode("utf-16-le"), mask.decode("latin-1").encode("utf-16-le"), 2)):
                size = MIN_FRAGMENT * step
                if len(form) <= size or value.isdigit():
                    anchors.setdefault(form, []).append((0, form, cover, step, value))
                    continue
                for offset in range(0, len(form) - size + 1, step):
                    anchors.setdefault(form[offset : offset + size], []).append((offset, form, cover, step, value))
        self.anchors = anchors
        if anchors:
            self.echo = re.compile(b"|".join(re.escape(anchor) for anchor in sorted(anchors, key=lambda anchor: (-len(anchor), anchor))))

    def fresh(self, value):
        if value in self.cache:
            return self.cache[value]
        counter = 0
        while True:
            digest = b""
            block = 0
            while len(digest) < len(value):
                digest += hmac.new(self.key, value + bytes([counter, block]), hashlib.sha256).digest()
                block += 1
            mask = render(value, digest)
            if mask != value or not any(chr(byte).isalnum() for byte in value):
                self.cache[value] = mask
                return mask
            counter += 1

    def canon(self, value):
        if len(value) >= 3:
            for other in self.learned:
                if other.startswith(value):
                    return self.fresh(other)[: len(value)]
                if other.endswith(value):
                    return self.fresh(other)[len(other) - len(value) :]
        return self.fresh(value)


def render(value, digest):
    shape, allowed = alphabet(value)
    hexdigits = bytes(sorted(byte for byte in allowed if chr(byte).isalnum()))
    output = bytearray()
    for index, byte in enumerate(value):
        pick = digest[index]
        if shape == "hex" and chr(byte).isalnum():
            output.append(hexdigits[pick % 16])
        elif 48 <= byte <= 57:
            output.append(48 + pick % 10)
        elif 65 <= byte <= 90:
            output.append(65 + pick % 26)
        elif 97 <= byte <= 122 or byte >= 128:
            output.append(97 + pick % 26)
        else:
            output.append(byte)
    return bytes(output)


def home_mask(name):
    return (HOME_PLACEHOLDER + b"_" * len(name))[: len(name)]


def find_spans(blob, masker, learn):
    spans = {rule: [] for rule in RULES}
    seen = set()
    for pattern in (ACCOUNT, ACCOUNT_TAIL):
        for match in pattern.finditer(blob):
            value = match.group(2)
            if keep(value) or match.start(2) in seen:
                continue
            seen.add(match.start(2))
            if not match.group(1) and not re.search(rb"[0-9]", value):
                continue
            if learn:
                masker.learn(value)
            else:
                spans["account"].append((match.start(2), match.end(2), masker.canon(value)))
    named = [(match.start(1), match.end(1)) for match in NAMED.finditer(blob)]
    named += backward(blob, OWNER, NAME_BYTES, 80, 1)
    for start, end in named:
        value = blob[start:end]
        if learn:
            masker.learn(value)
        else:
            spans["name"].append((start, end, masker.canon(value)))
    found = [(match.start(1), match.end(1), 1) for pattern in (URN, HUB, PROJECT) for match in pattern.finditer(blob)]
    found += [(match.start(1), match.end(1), 2) for match in URN_WIDE.finditer(blob)]
    found += [(start, end, 1) for marker in LINK for start, end in backward(blob, marker, LINK_BYTES, 256, 6)]
    for start, end, step in found:
        raw = blob[start:end]
        value = raw[::2] if step == 2 else raw
        if keep(value):
            continue
        if learn:
            masker.learn(value)
            continue
        mask = masker.canon(value)
        spans["urn"].append((start, end, mask.decode("latin-1").encode("utf-16-le") if step == 2 else mask))
    if learn:
        return spans
    for pattern, step in ((HOME, 1), (HOME_WIDE, 2)):
        for match in pattern.finditer(blob):
            raw = match.group(1)
            name = raw[::2] if step == 2 else raw
            if name in SHARED or name == home_mask(name):
                continue
            mask = home_mask(name)
            spans["home"].append((match.start(1), match.end(1), mask.decode("latin-1").encode("utf-16-le") if step == 2 else mask))
    spans["echo"] = echo_spans(blob, masker)
    return spans


def alphabet(value):
    alnum = bytes(byte for byte in value if chr(byte).isalnum())
    extra = bytes(sorted({byte for byte in value if not chr(byte).isalnum()}))
    if alnum and re.fullmatch(rb"[0-9a-f]+", alnum):
        return "hex", set(b"0123456789abcdef" + extra)
    if alnum and re.fullmatch(rb"[0-9A-F]+", alnum):
        return "hex", set(b"0123456789ABCDEF" + extra)
    if alnum.isdigit():
        return "digits", set(b"0123456789" + extra)
    return "text", set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" + extra)


def accept(blob, start, end, head, tail, shape):
    if head and tail:
        return True
    if shape == "digits":
        return False
    if shape == "hex" and end - start < MIN_HEX_FRAGMENT:
        if head and start > 0 and blob[start - 1 : start] in (b'"', b" "):
            return True
        return tail and blob[end : end + 1] == b'"'
    return True


def widen(blob, start, end, allowed, step):
    while start >= step and blob[start - step] in allowed and (step == 1 or blob[start - 1] == 0):
        start -= step
    while end + step <= len(blob) and blob[end] in allowed and (step == 1 or blob[end + 1] == 0):
        end += step
    return start, end


def echo_spans(blob, masker):
    found = set()
    if masker.echo is None:
        return []
    for match in masker.echo.finditer(blob):
        for offset, form, cover, step, value in masker.anchors[match.group(0)]:
            start, end = match.start(), match.end()
            low, high = offset, offset + (end - start)
            while low >= step and start >= step and blob[start - step : start] == form[low - step : low]:
                start, low = start - step, low - step
            while high + step <= len(form) and blob[end : end + step] == form[high : high + step]:
                end, high = end + step, high + step
            shape, allowed = alphabet(value)
            if not accept(blob, start, end, low == 0, high == len(form), shape):
                continue
            wide_start, wide_end = widen(blob, start, end, allowed, step)
            if (wide_start, wide_end) != (start, end):
                text = blob[wide_start:wide_end][::step]
                fresh = masker.fresh(text)
                found.add((wide_start, wide_end, fresh.decode("latin-1").encode("utf-16-le") if step == 2 else fresh))
            else:
                found.add((start, end, cover[low:high]))
    return sorted(found)


def apply_spans(blob, spans, counts):
    taken = []
    output = bytearray(blob)
    for rule in ("urn", "account", "name", "home", "echo"):
        for start, end, mask in sorted(spans[rule]):
            if any(start < other_end and other_start < end for other_start, other_end in taken):
                continue
            if len(mask) != end - start:
                raise ValueError("placeholder length differs from the replaced span")
            if blob[start:end] == mask:
                continue
            output[start:end] = mask
            taken.append((start, end))
            counts[rule] += 1
    return bytes(output)


class Entry:
    def __init__(self, blob, offset):
        fields = CENTRAL.unpack_from(blob, offset)
        if fields[0] != CENTRAL_SIG:
            raise ValueError("bad central directory signature")
        self.central = offset
        self.flags, self.method = fields[3], fields[4]
        self.crc, self.csize, self.usize = fields[7], fields[8], fields[9]
        self.length = CENTRAL.size + fields[10] + fields[11] + fields[12]
        self.local = fields[16]
        if 0xFFFFFFFF in (self.csize, self.usize, self.local):
            raise ValueError("ZIP64 members are not supported")
        if self.flags & 1:
            raise ValueError("encrypted members are not supported")
        local = LOCAL.unpack_from(blob, self.local)
        if local[0] != LOCAL_SIG:
            raise ValueError("bad local header signature")
        self.data = self.local + LOCAL.size + local[9] + local[10]
        self.tail = self.data + self.csize
        self.descriptor = 0
        if self.flags & 8:
            self.descriptor = 16 if blob[self.tail : self.tail + 4] == DESCRIPTOR_SIG else 12
        self.end = self.tail + self.descriptor


def read_member(blob, entry):
    data = blob[entry.data : entry.tail]
    if entry.method == zipfile.ZIP_STORED:
        payload = data
    elif entry.method == zipfile.ZIP_DEFLATED:
        payload = zlib.decompress(data, -15)
    elif entry.method == zipfile.ZIP_ZSTANDARD:
        payload = zstd.decompress(data)
    else:
        raise ValueError(f"unsupported compression method {entry.method}")
    if zlib.crc32(payload) != entry.crc or len(payload) != entry.usize:
        raise ValueError("member CRC or size mismatch")
    return payload


def write_member(payload, entry):
    if entry.method == zipfile.ZIP_STORED:
        return payload
    if entry.method == zipfile.ZIP_DEFLATED:
        packer = zlib.compressobj(DEFLATE_LEVELS[entry.flags & 6], zlib.DEFLATED, -15)
        return packer.compress(payload) + packer.flush()
    return zstd.compress(payload)


def parse_archive(blob):
    end = blob.rfind(END_SIG, max(0, len(blob) - 65557))
    if end < 0:
        raise ValueError("missing end of central directory")
    fields = END.unpack_from(blob, end)
    if end + END.size + fields[7] != len(blob):
        raise ValueError("unexpected bytes after the archive comment")
    if end >= 20 and blob[end - 20 : end - 16] == b"PK\x06\x07":
        raise ValueError("ZIP64 archives are not supported")
    entries = []
    cursor = fields[6]
    for _ in range(fields[4]):
        entry = Entry(blob, cursor)
        entries.append(entry)
        cursor += entry.length
    if cursor != end:
        raise ValueError("central directory does not end at the end record")
    return entries, fields[6], end


def walk_archive(blob, masker, counts, learn, depth):
    entries, directory, end = parse_archive(blob)
    output = bytearray()
    moved = {}
    position = 0
    changed = False
    for entry in sorted(entries, key=lambda item: item.local):
        if entry.local < position:
            raise ValueError("overlapping archive members")
        output += blob[position : entry.local]
        moved[entry.central] = len(output)
        position = entry.end
        payload = read_member(blob, entry)
        fresh = walk_payload(payload, masker, counts, learn, depth)
        if learn or fresh == payload:
            output += blob[entry.local : entry.end]
            continue
        changed = True
        packed = write_member(fresh, entry)
        crc = zlib.crc32(fresh)
        header = bytearray(blob[entry.local : entry.data])
        if not entry.flags & 8 or struct.unpack_from("<L", header, 14)[0]:
            struct.pack_into("<LLL", header, 14, crc, len(packed), len(fresh))
        descriptor = bytearray(blob[entry.tail : entry.end])
        if entry.descriptor:
            struct.pack_into("<LLL", descriptor, entry.descriptor - 12, crc, len(packed), len(fresh))
        output += header + packed + descriptor
        entry.crc, entry.csize, entry.usize = crc, len(packed), len(fresh)
    if learn or not changed:
        return blob
    output += blob[position:directory]
    start = len(output)
    for entry in entries:
        record = bytearray(blob[entry.central : entry.central + entry.length])
        struct.pack_into("<LLL", record, 16, entry.crc, entry.csize, entry.usize)
        struct.pack_into("<L", record, 42, moved[entry.central])
        output += record
    record = bytearray(blob[end:])
    struct.pack_into("<L", record, 16, start)
    output += record
    check_archive(blob, bytes(output))
    return bytes(output)


def walk_payload(payload, masker, counts, learn, depth):
    if payload[:4] == LOCAL_SIG and depth < MAX_DEPTH:
        return walk_archive(payload, masker, counts, learn, depth + 1)
    spans = find_spans(payload, masker, learn)
    if learn:
        return payload
    return apply_spans(payload, spans, counts)


def check_archive(before, after):
    fields = ("filename", "compress_type", "date_time", "external_attr", "internal_attr", "extra", "comment", "create_system", "create_version", "extract_version", "flag_bits")
    with zipfile.ZipFile(io.BytesIO(before)) as old, zipfile.ZipFile(io.BytesIO(after)) as new:
        if old.comment != new.comment:
            raise ValueError("archive comment changed")
        old_infos, new_infos = old.infolist(), new.infolist()
        if len(old_infos) != len(new_infos):
            raise ValueError("member count changed")
        for old_info, new_info in zip(old_infos, new_infos, strict=True):
            for field in fields:
                if getattr(old_info, field) != getattr(new_info, field):
                    raise ValueError(f"member {field} changed")
        if new.testzip() is not None:
            raise ValueError("rewritten archive fails its CRC check")


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ledger", type=Path)
    options = parser.parse_args()
    masker = Masker(secrets.token_bytes(32))
    blobs = {path: path.read_bytes() for path in options.paths}
    for path, blob in blobs.items():
        walk_archive(blob, masker, {rule: 0 for rule in RULES}, True, 0)
    masker.seal()
    rows = []
    for path, blob in blobs.items():
        counts = {rule: 0 for rule in RULES}
        fresh = walk_archive(blob, masker, counts, False, 0)
        summary = " ".join(f"{rule}={counts[rule]}" for rule in RULES)
        print(f"{path} {digest(blob)} {digest(fresh)} {summary}")
        if fresh == blob:
            continue
        rows.append({"path": path.as_posix(), "fusionSavedSha256": digest(blob), "committedSha256": digest(fresh), "counts": counts})
        if not options.dry_run:
            path.write_bytes(fresh)
    if options.ledger and not options.dry_run:
        ledger = json.loads(options.ledger.read_text()) if options.ledger.exists() else {"reason": REASON, "files": []}
        known = {row["path"]: row for row in ledger["files"]}
        for row in rows:
            prior = known.get(row["path"])
            if prior and prior["committedSha256"] == row["fusionSavedSha256"]:
                row["fusionSavedSha256"] = prior["fusionSavedSha256"]
                row["counts"] = {rule: prior["counts"][rule] + row["counts"][rule] for rule in RULES}
            known[row["path"]] = row
        ledger["files"] = [known[name] for name in sorted(known)]
        options.ledger.write_text(json.dumps(ledger, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
