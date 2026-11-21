from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from xml.etree.ElementTree import fromstring
from xml.parsers.expat import ParserCreate


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
BASE = "16c8f9c49112e532d834ee215fce32748c3fa138"
OWNERS = "0d21e27c454c2b4619c3db3106e2f167d0a28d9eb91e9a1cca90b05d7625ea5c"
DISCLOSED = "cb044d2a615d819e8ac642f3eea4bf5f313b8b61c5bd70570e7e3c90895a26f1"
DIAGNOSTIC = "a23e44a29967ad84e2716f66363c2898025460bd5a9dddf266e575bdac3a88d2"
SCHEMA = "kit.sw2026.disclosed-material-tree-correlation.v1"
STREAM = "swXmlContents/MATERIALTREE"
URI = "http://www.solidworks.com/sldmaterials"
MATERIAL = "/materials/classification[1]/material[1]"
PHYSICAL = MATERIAL + "/physicalproperties[1]"
SWATCH = MATERIAL + "/swatchcolor[1]"
CONFIG = "/materials/configurationslist[1]/configuration[1]"
SAVES = {"Author": "Original.SLDPRT", "Swap": "Swapped.SLDPRT", "Depth": "DepthEdit.SLDPRT"}
FIRST_A = "D01Corner/Author"
SECOND_A = "D02Center/Swap"
STEEL = "D01Corner/Swap"
IO_EVENTS = {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.fork", "os.posix_spawn",
             "subprocess.Popen", "ctypes.dlopen", "socket.connect"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def checked(root, relative, expected):
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),
            "disclosed input escaped the exact custody boundary")
    raw = path.read_bytes()
    require(digest(raw) == expected, "disclosed input hash differs: " + relative)
    return raw


def load_inputs(disclosed):
    require(disclosed.name == "SdkNamedMaterial01" and disclosed.is_dir() and not disclosed.is_symlink(),
            "expected only the disclosed named-material research directory")
    disclosed = disclosed.resolve()
    facts = json.loads(checked(ROOT, "re/solidworks/measurements/2026/AssignedMaterialArchiveOwners01.json", OWNERS))
    source = json.loads(checked(disclosed, "NativeSourcePacket03/Inspection/Result.json", DISCLOSED))
    control = json.loads(checked(disclosed, "NativeDensityProbe01/Native/Result.json", DIAGNOSTIC))
    require(source["passed"] is True and source["controls_healthy"] is True and source["distinct_native_processes"] == 10
            and control["complete_observations"] is True and control["controls_healthy"] is True
            and set(control["rows"]["Author"]["states"]) == {"unassigned", "assigned", "saved"},
            "prior source or diagnostic lifecycle did not pass")
    rows = {}
    for case in ("D01Corner", "D02Center"):
        for phase, basename in SAVES.items():
            role = f"{case}/{phase}"
            row = source["phases"][role]
            require(row["passed"] is True, "disclosed save did not pass")
            rows[role] = (f"NativeSourcePacket03/Inspection/{role}/{basename}", row["file"])
    rows["Diagnostic"] = ("NativeDensityProbe01/Native/AssignedDensityProbe.SLDPRT", control["rows"]["Author"]["file"])
    inputs = {}
    for role, (path, saved) in rows.items():
        logged = facts["cases"][role]
        require(saved["sha256"] == logged["file_sha256"] and saved["bytes"] == logged["file_bytes"]
                and saved["diagnostics"] == [True, 0, 0], "saved part differs from its typed-owner receipt")
        raw = checked(disclosed, path, saved["sha256"])
        require(len(raw) == saved["bytes"], "saved part length differs")
        inputs[role] = (raw, logged)
    return inputs


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def traverse(node, path="/materials"):
    yield path, node
    siblings = Counter()
    for child in node:
        name = local_name(child.tag)
        siblings[name] += 1
        yield from traverse(child, f"{path}/{name}[{siblings[name]}]")


def wire_order(blob):
    parser = ParserCreate(namespace_separator="|")
    parser.ordered_attributes = True
    open_elements = []
    rows = {}

    def refuse(*args):
        raise ValueError("unexpected XML document type or entity")

    def start(tag, attributes):
        name = tag.rsplit("|", 1)[-1]
        if open_elements:
            parent, counts = open_elements[-1]
            counts[name] += 1
            path = f"{parent}/{name}[{counts[name]}]"
        else:
            path = "/" + name
        rows[path] = (parser.CurrentByteIndex, tuple(
            "{" + key.replace("|", "}", 1) if "|" in key else key for key in attributes[::2]
        ))
        open_elements.append((path, Counter()))

    parser.StartElementHandler = start
    parser.EndElementHandler = lambda _: open_elements.pop()
    parser.StartDoctypeDeclHandler = parser.EntityDeclHandler = parser.ExternalEntityRefHandler = refuse
    parser.Parse(blob, True)
    return rows


def xml_model(blob):
    require(blob.startswith(b"\xff\xfe") and len(blob) % 2 == 0, "expected BOM-marked UTF-16LE XML")
    text = blob.decode("utf-16")
    require("<!DOCTYPE" not in text and "<!ENTITY" not in text, "unexpected XML declaration")
    doc = fromstring(text)
    require(doc.tag == "{" + URI + "}materials"
            and [local_name(child.tag) for child in doc] == ["curves", "classification", "configurationslist"],
            "unexpected typed material tree root")
    nodes = dict(traverse(doc))
    order = wire_order(blob)
    require(tuple(nodes) == tuple(order)
            and all(tuple(node.attrib) == order[path][1] for path, node in nodes.items()),
            "decoded typed XML differs from the observed wire order")
    return nodes, order


def identity(nodes, owners):
    row = nodes[MATERIAL]
    binding = nodes[CONFIG]
    text = owners["active_config_material"]
    catalog_material, number = text.rsplit("|", 1)
    require(re.fullmatch("[0-9]+", number) and row.attrib["matid"] == number
            and row.attrib["name"] == catalog_material
            and binding.attrib["name"] == "Default" and binding.attrib["material"] == text,
            "observed XML row and active configuration did not bind the actual binary IdName")
    value = float(nodes[PHYSICAL + "/DENS[1]"].attrib["value"])
    require(value == owners["active_config_density"] == owners["part_density"]["f58"],
            "XML DENS scalar differs from the typed configuration and part archive owners")
    return int(number)


def swatch_span(blob, nodes, position):
    decoded = nodes[SWATCH].attrib
    require(set(decoded) == {"RGB"} and re.fullmatch("[0-9a-fA-F]{6}", decoded["RGB"]),
            "unexpected swatchcolor type")
    wire = blob[position:].decode("utf-16-le")
    lexical = re.match(r'''<(?:[A-Za-z_][\w.-]*:)?swatchcolor[ \t\r\n]+RGB\s*=\s*(["'])([0-9a-fA-F]{6})\1\s*>''', wire)
    require(lexical and lexical.group(2) == decoded["RGB"], "RGB value is outside the observed start tag")
    begin, end = lexical.span(2)
    return position + 2 * begin, position + 2 * end


def element_signature(element):
    return element.tag, tuple(element.attrib.items()), element.text, element.tail


def compare_a(left, right):
    a, ga, oa = left
    b, gb, ob = right
    require(oa == ob and tuple(ga) == tuple(gb) and len(a) == len(b),
            "same-material tag ordering, attribute ordering, offsets or length differ")
    changed = [path for path, first in ga.items() if element_signature(first) != element_signature(gb[path])]
    require(changed == [SWATCH], "same-material comparison changes an unrelated XML element")
    first, second = ga[SWATCH], gb[SWATCH]
    require((first.tag, first.text, first.tail) == (second.tag, second.text, second.tail)
            and int(first.attrib["RGB"], 16) != int(second.attrib["RGB"], 16),
            "swatch difference is not one typed RGB value")
    begin, end = swatch_span(a, ga, oa[SWATCH][0])
    require((begin, end) == swatch_span(b, gb, ob[SWATCH][0])
            and a[:begin] == b[:begin] and a[end:] == b[end:] and end - begin == 12,
            "changed swatch value does not explain the full wire delta")
    offsets = [index for index in range(begin, end) if a[index] != b[index]]
    require(offsets == list(range(begin, end, 2)), "expected exactly six changed UTF-16LE low bytes")
    return {"changed_attribute": SWATCH + "/@RGB", "lexical_type": "six_ascii_hex_digits", "numeric_rgb_differs": True,
            "owner_start_byte_including_bom": oa[SWATCH][0],
            "stream_byte_interval_including_bom": [begin, end], "utf16_code_unit_interval_after_bom": [(begin - 2) // 2, (end - 2) // 2],
            "changed_byte_offsets": offsets, "byte_equal_outside_value": True, "identical_element_and_attribute_wire_order": True,
            "unchanged_config_association_and_physical_properties": True}


def counts(nodes):
    return {
        "elements": len(nodes),
        "direct_physical_property_children": len(nodes[PHYSICAL]),
        "curve_points": len(nodes["/materials/curves[1]"]),
        "active_configuration_rows": len(nodes["/materials/configurationslist[1]"]),
    }


def correlate(inputs, archive_type, logical_version):
    shapes, cases = {}, {}
    for role, (raw, logged) in inputs.items():
        archive = archive_type.from_bytes(raw)
        require(archive.format_version == 4 and logical_version(archive.streams) == 19000,
                "disclosed save no longer uses the measured native framing")
        blob = archive.require(STREAM)
        require(digest(blob) == logged["material_tree"]["sha256"] and len(blob) == logged["material_tree"]["bytes"],
                "material tree differs from the typed-owner receipt")
        nodes, order = xml_model(blob)
        cases[role] = {
            "file_sha256": digest(raw), "stream_sha256": digest(blob), "stream_bytes": len(blob),
            "xml_configuration_material_is_binary_id_name": True,
            "material_numeric_id": identity(nodes, logged["owners"]),
            "xml_density_equals_binary_part_and_active_configuration": True,
        }
        shapes[role] = (blob, nodes, order)
    a, alternate, b = (shapes[key] for key in (FIRST_A, SECOND_A, STEEL))
    contrast = compare_a(a, alternate)
    require(shapes["Diagnostic"][0] == a[0] and shapes["D02Center/Depth"][0] == alternate[0]
            and shapes["D01Corner/Depth"][0] == shapes["D02Center/Author"][0] == b[0],
            "same-assignment, depth-edit, diagnostic or second-design contrast changed")
    require(alternate[1][SWATCH].attrib["RGB"] == b[1][SWATCH].attrib["RGB"] and b[1][SWATCH].attrib["RGB"] != a[1][SWATCH].attrib["RGB"],
            "saved predecessor and cross-material swatch contrast changed")
    shared = set(a[1]) & set(b[1])
    extra = [key for key in b[1] if key not in shared]
    require(tuple(a[1]) == tuple(key for key in b[1] if key in shared)
            and all(a[2][key][1] == b[2][key][1] for key in shared)
            and all(key.startswith(PHYSICAL + "/") for key in extra) and len(extra) == 14,
            "cross-material relative wire order or optional property inventory changed")
    return {
        "cases": cases, "same_a_comparison": contrast,
        "identity_paths": {"material_id": MATERIAL + "/@matid", "material_catalog_name": MATERIAL + "/@name",
                           "configuration_material": CONFIG + "/@material", "density": PHYSICAL + "/DENS[1]/@value"},
        "tree_counts": {"A": counts(a[1]), "B": counts(b[1])},
        "b_only_physical_element_counts": dict(Counter(local_name(b[1][key].tag) for key in extra)),
        "a_b_common_element_and_attribute_wire_order": True,
        "independent_a_diagnostic_without_appearance_perturbation_matches_d01_author": True,
        "d02_a_swatch_matches_its_predecessor_b": True, "d01_b_swatch_differs_from_its_predecessor_a": True,
        "all_b_streams_equal": True, "both_depth_edits_preserve_full_tree_bytes": True,
    }


def measure(root):
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    inputs = load_inputs(root)
    proof = digest(HERE.read_bytes())
    for codec in ("ascii", "latin-1", "utf-16", "utf-16-le", "utf-8"):
        lookup(codec)
    active = True

    def guard(event, args):
        require(not active or event not in IO_EVENTS, "material tree analysis attempted an external read or launch")

    sys.addaudithook(guard)
    report = correlate(inputs, SldprtArchive, ContainerMo)
    active = False
    return {"schema": SCHEMA, "base_revision": BASE, "proof_sha256": proof, "stream": STREAM,
            "namespace": URI, "wire_encoding": "UTF-16LE with BOM",
            "disclosed_native_result_sha256": DISCLOSED, "diagnostic_native_result_sha256": DIAGNOSTIC,
            "typed_owner_receipt_sha256": OWNERS,
            "native_processes_started": 0, "protected_inputs_read": 0, "runtime_input_reads": 0,
            "xml_artifacts_emitted": 0, **report}


def main():
    parser = ArgumentParser()
    parser.add_argument("disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = encode(measure(args.disclosed))
    if args.output is None:
        sys.stdout.buffer.write(result)
    else:
        with args.output.open("xb") as output:
            output.write(result)
        print(digest(result))


if __name__ == "__main__":
    main()
