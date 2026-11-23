from struct import pack

from ProjectD01Concentric import require

from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount

OPEN_TIME = "docProps/OpenTime.xml"
OPEN_TIME_FIELDS = ("count", "TotalFileOpenTime", "LWcount", "LWTotalFileOpenTime")
OFFICE_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/"

ATTACHMENTS = "Contents/Config-0-Attachment"
OLE_CONTENTS = "Contents/OleItems"
OLE_ITEMS = "OleItemInformation/OLE_Item_Data"
MOTION_MAP = "ThirdPty/CMMotionLoadMapU"
MOTION_STUDY = "CM_MOTION_LOAD_1"
MOTION_LOAD = "ThirdPty/" + MOTION_STUDY
MOTION_SCHEDULES = "ThirdPty/SWA_Schedules"
MEMBERS = frozenset(
    {
        OPEN_TIME,
        ATTACHMENTS,
        OLE_CONTENTS,
        OLE_ITEMS,
        MOTION_MAP,
        MOTION_LOAD,
        MOTION_SCHEDULES,
    }
)


def empty_open_time():
    counts = (0, -1, 0, -1)
    lanes = "".join(
        f'<{name} xmlns="">{value}</{name}>'
        for name, value in zip(OPEN_TIME_FIELDS, counts, strict=True)
    )
    declaration = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    root = (
        f'<Properties xmlns="{OFFICE_NAMESPACE}SolidworksOpenTime" '
        f'xmlns:vt="{OFFICE_NAMESPACE}docPropsVTypes">'
    )
    return f"{declaration}\r\n{root}{lanes}</Properties>\r\n".encode("utf-8")


def motion_name_field(value, encoding, unit_size):
    encoded = value.encode(encoding)
    return pack("<I", len(encoded) // unit_size) + encoded


def default_motion_map():
    return (
        pack("<I", 1)
        + motion_name_field("Motion Study 1", "utf-16-le", 2)
        + motion_name_field(MOTION_STUDY, "ascii", 1)
    )


def fresh_assembly_auxiliaries():
    return {
        OPEN_TIME: empty_open_time(),
        ATTACHMENTS: EncodeCount(0),
        OLE_CONTENTS: pack("<I", 0),
        OLE_ITEMS: pack("<I", 0),
        MOTION_MAP: default_motion_map(),
        MOTION_LOAD: b"",
        MOTION_SCHEDULES: b"",
    }


def add_fresh_assembly_auxiliaries(streams):
    require(
        not MEMBERS.intersection(streams),
        "fresh assembly auxiliary members already have an owner",
    )
    return streams | fresh_assembly_auxiliaries()
