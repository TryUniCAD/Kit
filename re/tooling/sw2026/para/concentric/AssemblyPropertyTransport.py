from dataclasses import dataclass
import re
from xml.etree.ElementTree import Element, SubElement

from D01AssemblyPropertyIntent import CORE, CUSTOM
from ProjectD01Concentric import require

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.CheckPropText import CheckPropText
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.WritePropXml import WritePropXml
from convert.adapters.solidworks.Container.Format import KContentTypesStream, KRelationshipsStream
from convert.adapters.solidworks.Core.Native import EncodeNativeXml
from convert.adapters.solidworks.Core.Properties.ReadCoreProps import ReadCoreProps
from convert.adapters.solidworks.Core.Properties.ReadCustomProps import ReadCustomProps
from convert.adapters.solidworks.Core.Properties.ReadPropRoot import ReadPropRoot
from convert.adapters.solidworks.Drawing.Metadata.Writing.PropertyVocabulary import KPropertyValueNamespace


APP = "docProps/app.xml"
TRANSPORT = (KContentTypesStream, KRelationshipsStream, APP)
OPC = "http://schemas.openxmlformats.org/package/2006/"
OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/"
TYPES_NAMESPACE = OPC + "content-types"
RELS_NAMESPACE = OPC + "relationships"
APP_NAMESPACE = OFFICE + "extended-properties"
PACKAGE_MIME = "application/vnd.openxmlformats-package."
OFFICE_MIME = "application/vnd.openxmlformats-officedocument."
APP_FIELDS = (
    "Template", "TotalTime", "Application", "DocSecurity", "Company",
    "LinksUpToDate", "SharedDoc", "HyperlinksChanged", "AppVersion",
)
PROPERTY_ROLES = {
    CORE: (OPC + "relationships/metadata/core-properties", PACKAGE_MIME + "core-properties+xml"),
    APP: (OFFICE + "relationships/extended-properties", OFFICE_MIME + "extended-properties+xml"),
    CUSTOM: (OFFICE + "relationships/custom-properties", OFFICE_MIME + "custom-properties+xml"),
}


@dataclass(frozen=True, slots=True)
class ApplicationProperties:
    application: str
    version: str
    template: str
    company: str
    edit_minutes: int

    def __post_init__(self):
        CheckPropText(self.application)
        for value in (self.template, self.company):
            if value != "":
                CheckPropText(value)
        require(type(self.version) is str and re.fullmatch(r"[0-9]{1,5}\.[0-9]{4}", self.version) is not None,
                "application version requires the observed decimal representation")
        require(type(self.edit_minutes) is int and 0 <= self.edit_minutes <= 0x7FFFFFFF,
                "application edit time requires nonnegative whole minutes")


def write_application_properties(intent):
    require(type(intent) is ApplicationProperties, "extended properties require typed application metadata")
    root = Element("Properties", {"xmlns": APP_NAMESPACE, "xmlns:vt": KPropertyValueNamespace})
    values = (intent.template, str(intent.edit_minutes), intent.application, "0", intent.company,
              "false", "false", "false", intent.version)
    for name, value in zip(APP_FIELDS, values, strict=True):
        SubElement(root, name).text = value
    return WritePropXml(root)


def read_application_properties(payload):
    root = ReadPropRoot(payload)
    ns = "{" + APP_NAMESPACE + "}"
    require(root.tag == ns + "Properties" and not root.attrib
            and tuple(row.tag for row in root) == tuple(ns + name for name in APP_FIELDS)
            and all(not row.attrib and not len(row) for row in root),
            "unsupported extended property owner or field")
    template, minutes, app, policy, company, links, shared, hyperlinks, version = (
        row.text or "" for row in root
    )
    require((policy, links, shared, hyperlinks) == ("0", "false", "false", "false"),
            "unsupported extended property security or shared-link state")
    require(re.fullmatch(r"(0|[1-9][0-9]{0,9})", minutes) is not None,
            "application editing time is outside the scoped integer profile")
    return ApplicationProperties(app, version, template, company, int(minutes))


def property_targets(streams):
    if CORE in streams:
        ReadCoreProps(streams[CORE])
    if CUSTOM in streams:
        ReadCustomProps(streams[CUSTOM], False)
    return frozenset((APP,)) | (streams.keys() & {CORE, CUSTOM})


def type_rows(targets):
    rows = (
        ("Default", {"Extension": "rels", "ContentType": PACKAGE_MIME + "relationships+xml"}),
        ("Default", {"Extension": "xml", "ContentType": PROPERTY_ROLES[APP][1]}),
    )
    return rows + tuple(("Override", {"PartName": "/" + part, "ContentType": PROPERTY_ROLES[part][1]})
                        for part in (CORE, CUSTOM) if part in targets)


def relationship_rows(targets):
    ids = {part: "rId" + str(index) for index, part in enumerate(PROPERTY_ROLES, 2)}
    return tuple(("Relationship", {"Id": ids[part], "Type": PROPERTY_ROLES[part][0], "Target": part})
                 for part in (APP, CORE, CUSTOM) if part in targets)


def write_index(root_name, namespace, rows, declaration):
    root = Element(root_name, {"xmlns": namespace})
    for name, values in rows:
        SubElement(root, name, values)
    return declaration + b"\r\n" + EncodeNativeXml(root).replace(b" />", b"/>") + b"\r\n"


def check_index(payload, root_name, namespace, expected):
    root = ReadPropRoot(payload)
    prefix = "{" + namespace + "}"
    require(root.tag == prefix + root_name and not root.attrib and len(root) == len(expected)
            and all(row.tag == prefix + name and row.attrib == attributes and not len(row)
                    and not (row.text or "").strip()
                    for row, (name, attributes) in zip(root, expected, strict=True)),
            "property package index differs from its actual typed targets or declarations")


def add_property_transport(streams, intent):
    require(not streams.keys() & set(TRANSPORT), "property transport already has an emitted stream")
    targets = property_targets(streams)
    return streams | {
        KContentTypesStream: write_index("Types", TYPES_NAMESPACE, type_rows(targets), b'<?xml version="1.0"?>'),
        KRelationshipsStream: write_index(
            "Relationships", RELS_NAMESPACE, relationship_rows(targets),
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'),
        APP: write_application_properties(intent),
    }


def read_property_transport(streams):
    require(set(TRANSPORT) <= streams.keys(), "property transport is incomplete")
    targets = property_targets(streams)
    check_index(streams[KContentTypesStream], "Types", TYPES_NAMESPACE, type_rows(targets))
    links = relationship_rows(targets)
    check_index(streams[KRelationshipsStream], "Relationships", RELS_NAMESPACE, links)
    return read_application_properties(streams[APP]), tuple(row["Target"] for _, row in links)
