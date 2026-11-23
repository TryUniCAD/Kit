from dataclasses import dataclass
from re import fullmatch


@dataclass(frozen=True)
class StringRow:
    flags: int
    references: tuple[int, ...]
    literal: str


@dataclass(frozen=True)
class NameSeed:
    geometry: int
    endpoint: int | None
    string_ids: tuple[int, ...]
    suffixes: tuple[str, ...]


def bounded_hex(text):
    if fullmatch("[0-9a-f]{1,8}", text) is None:
        raise ValueError("invalid element string hexadecimal selector")
    return int(text, 16)


def count_text(text):
    if fullmatch("(0|[1-9][0-9]{0,3})", text) is None:
        raise ValueError("invalid element table decimal field")
    return int(text)


def read_string_table(data):
    if not 0 < len(data) < 16384:
        raise ValueError("unsupported element string table size")
    header, *lines = data.decode("ascii").splitlines()
    magic, version, bound = header.split()
    if (magic, version) != ("StringTableStart", "v1") or len(lines) != count_text(
        bound
    ):
        raise ValueError("invalid element string table framing")
    result = {}
    last_id = 0
    previous = ()
    for line in lines:
        record, _, payload = line.partition(" ")
        encoded_id, flag_hex, *encoded_refs = record.split(".")
        relative = encoded_id.startswith("-")
        identity = (
            bounded_hex(encoded_id[1:]) + last_id
            if relative
            else bounded_hex(encoded_id)
        )
        if identity <= last_id:
            raise ValueError("nonincreasing element string identity")
        flags = bounded_hex(flag_hex)
        refs = []
        for index, text in enumerate(encoded_refs):
            if relative and index < len(previous):
                delta = (
                    -bounded_hex(text[1:])
                    if text.startswith("-")
                    else bounded_hex(text)
                )
                key = previous[index] + delta
            else:
                scalar = bounded_hex(text)
                key = identity - scalar if relative else scalar
            if key not in result:
                raise ValueError("dangling element string dependency")
            refs.append(key)
        if flags == 0:
            if refs or not payload.startswith("0:") or not payload[2:].isprintable():
                raise ValueError("unsupported literal element string")
            literal = payload[2:]
        elif flags == 0x0C:
            if len(refs) != 1 or not payload.isalnum():
                raise ValueError("unsupported literal element string postfix")
            literal = payload
        elif flags in (0x1C, 0x2C, 0x4C):
            if len(refs) != 2 or payload:
                raise ValueError("unsupported combined element string")
            literal = ""
        else:
            raise ValueError("unknown element string flags")
        if refs and result[refs[0]].flags != 0:
            raise ValueError("element string postfix is not a literal owner")
        row = StringRow(flags, tuple(refs), literal)
        result[identity] = row
        last_id, previous = identity, row.references
    return result


def read_geometry_seed(value, ids=(), suffixes=()):
    match = fullmatch(r"g([1-9][0-9]{0,3})(?:v([12]))?", value)
    if match is None:
        raise ValueError("element name lacks a bounded sketch geometry seed")
    geometry, endpoint = match.groups()
    return NameSeed(
        int(geometry), None if endpoint is None else int(endpoint), ids, suffixes
    )


def resolve_seed(table, identity, index, limit=12):
    if not limit or identity not in table:
        raise ValueError("element name points outside its local string table")
    row = table[identity]
    flags, refs = row.flags, row.references
    if flags == 0:
        return read_geometry_seed(row.literal, (identity,))
    suffix = table[refs[0]].literal
    if flags == 0x0C:
        if index:
            raise ValueError("literal sketch seed has an unexpected subindex")
        return read_geometry_seed(row.literal, (identity, *refs), (suffix,))
    if flags == 0x1C:
        literal = table[refs[1]]
        if not index or literal.flags != 0:
            raise ValueError("indexed sketch seed lacks its real literal")
        return read_geometry_seed(
            literal.literal + str(index), (identity, *refs), (suffix,)
        )
    if flags == 0x4C and not index:
        raise ValueError("element selector lacks its stored prefix subindex")
    parent = resolve_seed(table, refs[1], index if flags == 0x4C else 0, limit - 1)
    return NameSeed(
        parent.geometry,
        parent.endpoint,
        (identity, refs[0], *parent.string_ids),
        (*parent.suffixes, suffix),
    )
