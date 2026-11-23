from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from xml.etree.ElementTree import Element, SubElement

from ProjectD01Concentric import require

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.CheckPropText import CheckPropText
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakeCustomProps import MakeCustomProps
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PropertyNames import KSummaryNamespaces
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.WritePropXml import WritePropXml
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Properties.ManagerFields import KManagerFields, KManagerSchemas
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, RequireNode
from convert.adapters.solidworks.Core.Properties.ReadPropRoot import ReadPropRoot


MANAGER = "Contents/CusProps"
CORE = "docProps/core.xml"
CUSTOM = "docProps/custom.xml"
CONFIG = "docProps/Config-0-Properties.xml"
SCOPE_KEYS = frozenset((MANAGER, CORE, CUSTOM, CONFIG))
ASSY_FILE = "moAssyFilePropContainer_c"
XML_PROVENANCE = (
    ("dc:lastModifiedBy", "{" + KSummaryNamespaces["xmlns:dc"] + "}lastModifiedBy"),
    ("dcterms:created", "{" + KSummaryNamespaces["xmlns:dcterms"] + "}created"),
    ("dcterms:modified", "{" + KSummaryNamespaces["xmlns:dcterms"] + "}modified"),
)


@dataclass(frozen=True, slots=True)
class AssemblyPropertyIntent:
    configuration: str
    created_at: int
    save_actor: str


def context():
    return BodyContext(
        19000, KManagerFields | {ASSY_FILE: KManagerFields["moFilePropContainer_c"]},
        {}, KManagerSchemas | {ASSY_FILE: (1,)},
    )


def read_property_manager(payload):
    def read_owned(ctx, reader, node):
        allowed = ("moCusPropMgr_c", "moCusPropContainer_c", ASSY_FILE)
        depth = reader.NestingDepth
        require(1 <= depth <= len(allowed) and node.ClassValue == RuntimeClass(allowed[depth - 1], 1),
                "assembly property manager has an unsupported concrete owner or placement")
        ReadBodyMut(ctx, reader, node)

    reader = GraphReader(BinaryReader(payload), ArchiveMaps(1), partial(read_owned, context()),
                         RequireCanonicalTags=True)
    root = ReadNodeMut(reader)
    fields = RequireNode(root, "moCusPropMgr_c").FieldsValue
    require(not reader.Cursor.GetRemaining() and
            (fields["f0c"], fields["f08"], fields["n20"], fields["f54"]) == (-1, 1, 1, 0),
            "assembly property manager is outside the empty keyed profile")
    row, = fields["f20"]
    require(row["key"] == 0, "assembly property manager lacks its actual file key")
    container = RequireNode(row["o"], "moCusPropContainer_c").FieldsValue
    file = RequireNode(container["f08"], ASSY_FILE).FieldsValue
    require((container["f10"], container["f18"], container["f20"]) == (None, None, 0)
            and file["f08"] is file["f10"] is None,
            "assembly property manager has a populated or competing owner")
    return reader.MapValue.CounterValue


def make_property_manager():
    file = ArchiveNode(RuntimeClass(ASSY_FILE, 1), {"f08": None, "f10": None})
    container = ArchiveNode(RuntimeClass("moCusPropContainer_c", 1),
                            {"f08": file, "f10": None, "f18": None, "f20": 0})
    root = ArchiveNode(RuntimeClass("moCusPropMgr_c", 1),
                       {"f0c": -1, "f08": 1, "f20": ({"key": 0, "o": container},), "f54": 0})
    writer = BodyWriter(ArchiveMaps(1), context(), WriteBodyMut)
    WriteNodeMut(writer, root)
    return bytes(writer.OutputValue)


def iso_utc(value):
    require(type(value) is int and 0 < value <= 0xFFFFFFFF,
            "assembly package event must be a positive whole UTC second")
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def utc_seconds(text):
    require(isinstance(text, str) and text.endswith("Z"), "assembly package clock is not UTC")
    result = int(datetime.fromisoformat(text).timestamp())
    require(iso_utc(result) == text, "assembly package clock is not a canonical whole UTC second")
    return result


def make_core(intent, modified_at):
    created = iso_utc(intent.created_at)
    modified = iso_utc(modified_at)
    actor = CheckPropText(intent.save_actor)
    require(intent.created_at <= modified_at, "assembly package creation follows its final save")
    core = Element("cp:coreProperties", KSummaryNamespaces)
    for (tag, _), value in zip(XML_PROVENANCE, (actor, created, modified), strict=True):
        SubElement(core, tag).text = value
    return WritePropXml(core)


def read_core(payload):
    root = ReadPropRoot(payload)
    require(root.tag == "{" + KSummaryNamespaces["xmlns:cp"] + "}coreProperties"
            and not root.attrib
            and tuple(node.tag for node in root) == tuple(tag for _, tag in XML_PROVENANCE)
            and all(not node.attrib and not len(node) for node in root),
            "assembly summary contains unprojected fields or noncanonical provenance")
    actor, created, modified = (node.text for node in root)
    return CheckPropText(actor), utc_seconds(created), utc_seconds(modified)


def configuration_and_save(config, headers):
    require(len(headers) == 2 and all(header.ClassValue == RuntimeClass("moHeader_c", 1) for header in headers),
            "assembly properties require both actual document headers")
    fields = RequireNode(config, "moConfiguration_c").FieldsValue
    name = ReadNodeName(config)
    file_refs = tuple(RequireNode(header.FieldsValue["f38"], "moExtObject_c") for header in headers)
    require(type(fields["f08"]) is int and fields["f08"] == 0 and name.strip()
            and all(file.FieldsValue["shared"]["f20"] == 3
                    and file.FieldsValue["shared"]["f28"] == header.FieldsValue["f70"]
                    and file.FieldsValue["refcfg"] == {"f08": CStringValue(name, True), "f10": fields["f08"]}
                    for file, header in zip(file_refs, headers, strict=True))
            and file_refs[0].FieldsValue["f60"] == file_refs[1].FieldsValue["f60"],
            "assembly text lacks its exact selected configuration and paired self-file save owner")
    return name, file_refs[0].FieldsValue["f60"]


def add_property_streams(streams, config, headers, intent):
    name, modified_at = configuration_and_save(config, headers)
    require(intent.configuration == name, "assembly property intent selects a different configuration")
    require(not streams.keys() & SCOPE_KEYS
            and not any(key.startswith("docProps/Config-") for key in streams),
            "assembly properties conflict with an already emitted scope")
    return streams | {MANAGER: make_property_manager(), CORE: make_core(intent, modified_at),
                      CUSTOM: MakeCustomProps((), False), CONFIG: MakeCustomProps((), True)}
