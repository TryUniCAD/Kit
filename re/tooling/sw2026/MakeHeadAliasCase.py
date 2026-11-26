from struct import pack

from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderFields, KHeaderScalars
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Container.Container import BuildSldprt


SELF = ("AliasSelf", "RootConfig", 301)
DIRECTORY = (("ZuluRef", "ZuluConfig", 923), ("AlphaRef", "AlphaConfig", 117))
DECOY = ("StandaloneDecoy", "DecoyConfig", 2)
PATH = "CaseParts"


def node(class_name, fields):
    return ArchiveNode(RuntimeClass(class_name, 1), fields)


def text_handle(value):
    return node("moCStringHandle_c", {"value": CStringValue(value, True)})


def file_owner(spec, location):
    name, configuration, file_word = spec
    blank = CStringValue("", True)
    return node("moExtObject_c", {
        "shared": {
            "h18": location, "h10": text_handle(name),
            "f20": 2, "f08": 0, "f28": 0,
            "f38": blank, "f40": blank, "f50": blank, "f35": 0,
        },
        "f58": 0, "f60": 0, "f48": file_word, "f4c": 0, "f78": 0,
        "refcfg": {"f08": CStringValue(configuration, True), "f10": 0},
        "f54": 0, "f70": 0, "f50": 0,
    })


def header(self_spec, directory_specs):
    location = text_handle(PATH)
    fields = {field: 0 if kind in KHeaderScalars else None for field, kind in KHeaderFields}
    if directory_specs:
        items = tuple(file_owner(spec, location) for spec in directory_specs)
        fields["f30"] = node("moExtObjectList_c", {"items": items})
    fields["f38"] = file_owner(self_spec, location)
    return WriteHeadGraph(node("moHeader_c", fields), 19000)


def authored_lanes():
    name = b"moPart_c"
    light_beginning = pack("<iI", 0, 19000)
    config_start = pack("<3H", 0xFFFF, 1, len(name)) + name + pack("<I", len(light_beginning))
    return {
        "Contents/Config-0": config_start + light_beginning,
        "Contents/Config-0-ModelHeader": header(SELF, DIRECTORY),
        "Header2": header(DECOY, ()),
    }


def frame_lanes(lanes, archive_version):
    return BuildSldprt({**lanes, f"_MO_VERSION_{archive_version}": b""}, FormatVersion=4)
