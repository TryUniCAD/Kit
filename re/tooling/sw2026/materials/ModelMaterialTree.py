from dataclasses import dataclass, field
import re
from xml.parsers.expat import ParserCreate
from xml.sax.saxutils import escape, unescape


NAME = r"[A-Za-z_][A-Za-z0-9_.-]*(?::[A-Za-z_][A-Za-z0-9_.-]*)?"
ATTR = rf' ({NAME})="([^"<>]*)"'
START = re.compile(rf"<(?P<name>{NAME})(?P<fields>(?:{ATTR})*)/?>")
ATTRIBUTE = re.compile(ATTR)
DECLARATION = '<?xml version="1.0"?>\r\n'
BOM = b"\xff\xfe"
ROOT = "mstns:materials"
PARENTS = ("curves", "classification", "configurationslist")
QUOTES = {'"': "&quot;"}


@dataclass(frozen=True, slots=True)
class MaterialElement:
    name: str
    attributes: tuple[tuple[str, str], ...] = ()
    children: tuple["MaterialElement", ...] = ()


@dataclass(slots=True)
class OpenElement:
    name: str
    attributes: tuple[tuple[str, str], ...]
    children: list[MaterialElement] = field(default_factory=list)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decode_attributes(source, cursor, name, ordered):
    source_text = source[cursor:].decode("utf-16-le")
    start = START.match(source_text)
    require(start is not None and start.group("name") == name, "material element has noncanonical syntax")
    rows = tuple((field, unescape(value, {"&quot;": '"', "&apos;": "'"}))
                 for field, value in ATTRIBUTE.findall(start.group("fields")))
    require([item for name, value in rows for item in (name, value.replace("\n", " "))] == ordered,
            "material attribute text differs from the XML parser")
    require(all("\r" not in value and "\t" not in value and (field == "appdata" or "\n" not in value)
                for field, value in rows), "material attribute uses unsupported whitespace")
    return rows


def validate_tree(model):
    require(model.name == ROOT and tuple(child.name for child in model.children) == PARENTS,
            "material tree root or child ownership differs")
    namespaces = dict(model.attributes)
    require(namespaces.get("xmlns:mstns") == "http://www.solidworks.com/sldmaterials",
            "unexpected material tree namespace")


def read_material_tree(source):
    require(source.startswith(BOM) and source[2:].startswith(DECLARATION.encode("utf-16-le")),
            "material tree has noncanonical UTF-16LE framing")
    parser = ParserCreate()
    parser.ordered_attributes = True
    stack = []
    roots = []

    def start(name, attributes):
        stack.append(OpenElement(name, decode_attributes(source, parser.CurrentByteIndex, name, attributes)))

    def finish(name):
        node = stack.pop()
        require(node.name == name, "material element stack differs")
        model = MaterialElement(node.name, node.attributes, tuple(node.children))
        (stack[-1].children if stack else roots).append(model)

    def data(text):
        require(not text.strip(), "material tree has unexpected text nodes")

    def refuse(*args):
        raise ValueError("material tree has unexpected XML markup")

    parser.StartElementHandler = start
    parser.EndElementHandler = finish
    parser.CharacterDataHandler = data
    parser.StartDoctypeDeclHandler = parser.EntityDeclHandler = parser.ExternalEntityRefHandler = refuse
    parser.CommentHandler = parser.ProcessingInstructionHandler = parser.StartCdataSectionHandler = refuse
    parser.Parse(source, True)
    require(not stack and len(roots) == 1, "material tree has invalid structure")
    validate_tree(roots[0])
    return roots[0]


def material_lines(model, depth=0, parent=None):
    require(re.fullmatch(NAME, model.name) is not None, "invalid material element name")
    names = tuple(name for name, _ in model.attributes)
    require(len(names) == len(set(names)) and all(re.fullmatch(NAME, name) for name in names),
            "invalid material attribute names")
    require(all(isinstance(value, str) and all(ord(char) >= 32 or char == "\n" for char in value)
                and (name == "appdata" or "\n" not in value) for name, value in model.attributes),
            "material attribute has invalid text")
    indentation = "\t" if parent == "curves" else "    " * max(0, depth - 1)
    opening = indentation + "<" + model.name
    fields = (f' {name}="{escape(value, QUOTES)}"' for name, value in model.attributes)
    opening += "".join(fields)
    if not model.children:
        yield opening + "/>"
        return
    yield opening + ">"
    for child in model.children:
        yield from material_lines(child, depth + 1, model.name)
    yield indentation + "</" + model.name + ">"


def emit_material_tree(model):
    validate_tree(model)
    wire = DECLARATION + "\r\n".join(material_lines(model)) + "\r\n"
    return BOM + wire.encode("utf-16-le")
