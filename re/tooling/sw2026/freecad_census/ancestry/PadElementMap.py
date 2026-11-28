from dataclasses import dataclass

from PadNameTable import bounded_hex, count_text


@dataclass(frozen=True)
class ElementName:
    literal: str
    string_id: int
    index: int
    postfix: str
    related_ids: tuple[int, ...]


@dataclass(frozen=True)
class ChildRange:
    first: int
    offset: int
    count: int
    tag: int
    map_index: int
    postfix: str


@dataclass(frozen=True)
class ElementGroup:
    kind: str
    children: tuple[ChildRange, ...]
    names: tuple[tuple[ElementName, ...], ...]


@dataclass(frozen=True)
class ElementMap:
    identity: int
    groups: tuple[ElementGroup, ...]


def read_entry(text, postfixes, table):
    prefix, pointer, *other = text.split(".")
    postfix_index = bounded_hex(pointer)
    if postfix_index > len(postfixes):
        raise ValueError("element name points outside its real postfix table")
    tail = postfixes[postfix_index - 1] if postfix_index else ""
    refs = tuple(bounded_hex(key) for key in other)
    if any(key not in table for key in refs):
        raise ValueError("element name has a dangling related string")
    if prefix.startswith("$#"):
        raw_id, separator, raw_index = prefix[2:].partition(":")
        identity = bounded_hex(raw_id)
        if identity not in table:
            raise ValueError("element name has a dangling hashed prefix")
        return ElementName(
            "", identity, bounded_hex(raw_index) if separator else 0, tail, refs
        )
    if not prefix.startswith(";") or not prefix[1:].isalnum():
        raise ValueError("unsupported local element name prefix")
    return ElementName(prefix[1:], 0, 0, tail, refs)


def take_count(lines, title):
    actual, count = next(lines).split()
    if actual != title:
        raise ValueError(f"expected element map {title} owner")
    return count_text(count)


def read_child(line, group_index):
    a, b, c, d, e, postfix, related = line.split()
    first, offset, count, tag, map_index = map(count_text, (a, b, c, d, e))
    if not count or not tag or not 0 < map_index < group_index or related != "0":
        raise ValueError("unsupported element map child range or association")
    return ChildRange(first, offset, count, tag, map_index, postfix)


def read_groups(lines, count, group_index, postfixes, table):
    result = []
    for _ in range(count):
        label = next(lines)
        if label not in ("Edge", "Face", "Vertex") or any(
            row.kind == label for row in result
        ):
            raise ValueError("duplicate or unsupported element shape group")
        children = tuple(
            read_child(next(lines), group_index)
            for _ in range(take_count(lines, "ChildCount"))
        )
        names = []
        for _ in range(take_count(lines, "NameCount")):
            words = next(lines).split()
            if words[-1:] != ["0"] or "0" in words[:-1]:
                raise ValueError("element name row does not exhaust its owned list")
            names.append(
                tuple(read_entry(value, postfixes, table) for value in words[:-1])
            )
        result.append(ElementGroup(label, children, tuple(names)))
    return tuple(result)


def parse_map(data, table):
    if not 0 < len(data) < 16384:
        raise ValueError("unsupported element map size")
    lines = iter(
        line.strip() for line in data.decode("ascii").splitlines() if line.strip()
    )
    try:
        if next(lines) != "BeginElementMap v1":
            raise ValueError("unsupported element map version")
        identity, title, count = next(lines).split()
        if title != "PostfixCount":
            raise ValueError("missing actual element postfix table")
        postfixes = tuple(next(lines) for _ in range(count_text(count)))
        map_count = take_count(lines, "MapCount")
        if not 0 < map_count <= 2 or len(set(postfixes)) != len(postfixes):
            raise ValueError("unsupported element map or postfix inventory")
        maps = []
        for index in range(1, map_count + 1):
            label, order, scoped_id, kinds = next(lines).split()
            if (
                label != "ElementMap"
                or count_text(order) != index
                or count_text(kinds) not in (2, 3)
            ):
                raise ValueError("invalid owned element map record")
            record = ElementMap(
                count_text(scoped_id),
                read_groups(lines, count_text(kinds), index, postfixes, table),
            )
            if next(lines) != "EndMap" or any(
                other.identity == record.identity for other in maps
            ):
                raise ValueError(
                    "element map record has a repeated identity or dangling extent"
                )
            maps.append(record)
        if maps[-1].identity != count_text(identity) or next(lines, None) is not None:
            raise ValueError("element map has a different root or trailing records")
        return tuple(maps)
    except StopIteration as error:
        raise ValueError("truncated element map") from error
