from datetime import datetime, timedelta, timezone
from pathlib import PureWindowsPath

from AssemblyContentIndex import native_path
from ConfigHeaderExchangeModel import project_active_config
from D01AssemblyPropertyIntent import CORE, read_core
from ObserveAssemblyUnitOwners import MONTHS, WEEKDAYS
from PartInformation import (
    EncodeInfoTable,
    KDictOrder,
    KInfoNames,
    KInfoXml,
    KInvalidXml,
)

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Units.MakeDualLength import (
    MakeDualLength,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KLengthCodes,
)
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Units.ReadPartUnitNodes import (
    ReadUnitNodes,
)

ASSEMBLY_KIND = "Assembly type"
ASSEMBLY_NAMES = (*KInfoNames[:16], ASSEMBLY_KIND, *KInfoNames[16:])
ASSEMBLY_DICT_ORDER = (19, *(pid + int(pid >= 19) for pid in KDictOrder if pid != 50))


def long_date(local):
    return f"{WEEKDAYS[local.weekday()]}, {MONTHS[local.month-1]} {local.day}, {local.year:04d}"


def long_timestamp(local):
    meridian = "AM" if local.hour < 12 else "PM"
    return f"{long_date(local)} {local.hour % 12 or 12}:{local.minute:02d}:{local.second:02d} {meridian}"


def system_values(archive, root, output, offset_minutes):
    path = PureWindowsPath(output)
    if path.suffix.casefold() != ".sldasm" or not path.stem:
        raise ValueError("assembly information needs its actual output filename")
    if type(offset_minutes) is not int or not -720 <= offset_minutes <= 840:
        raise ValueError("assembly information needs explicit local clock ownership")
    zone = timezone(timedelta(minutes=offset_minutes))
    actor, created_at, saved_at = read_core(archive.require(CORE))
    if created_at > saved_at:
        raise ValueError("assembly information creation follows publication")
    created, saved = (
        datetime.fromtimestamp(event, zone) for event in (created_at, saved_at)
    )
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    title, previous = native_path(header.FieldsValue["f38"], 3)
    if title != ReadNodeName(root):
        raise ValueError("assembly information root and document titles disagree")
    folder = (
        str(PureWindowsPath(previous).parent).rstrip("\\") + "\\" if previous else ""
    )
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
    configuration = project_active_config(manager)
    return {
        "SW-File Name": path.stem,
        "SW-BOM Part Number": title,
        "SW-Folder Name": folder,
        "SW-Short Date": f"{saved.month:02d}/{saved.day:02d}/{saved.year:04d}",
        "SW-Long Date": long_date(saved),
        "SW-Configuration Name": ReadNodeName(configuration),
        "SW-Author": "",
        "SW-Keywords": "",
        "SW-Comments": "",
        "SW-Title": "",
        "SW-Subject": "",
        "SW-Created Date": long_timestamp(created),
        "SW-Last Saved Date": long_timestamp(saved),
        "SW-Last Saved By": actor,
        "SW-File Title": "",
        "V_WorldOrientation": 1,
        ASSEMBLY_KIND: False,
        "SW-HasDesignTable": 0,
        "IsCPReArchEnabled": 1,
        "Component Type": 0,
    }


def unit_values(root):
    units = ReadUnitNodes(root)
    length = units["length"].FieldsValue
    angle = units["angle"].FieldsValue
    density = units["density"].FieldsValue
    primary_code = FieldInt(length, "fb0")
    alternate = length.get("fb8")
    if alternate is None:
        (primary,) = (
            unit for unit, code in KLengthCodes.items() if code == primary_code
        )
        alternate = MakeDualLength(primary)
    dual = RequireNode(alternate, units["length"].ClassValue.NameValue).FieldsValue
    if (
        FieldInt(density, "has_fb8")
        or FieldInt(density, "fcc") not in (0, 1)
        or FieldInt(density, "fc0") != FieldInt(density, "fc8")
    ):
        raise ValueError(
            "assembly information needs the ordinary inherited mass length and volume"
        )
    return {
        "SW_UnitSystem": FieldInt(units["unit_system"].FieldsValue, "fb0") + 1,
        "SW_UnitsLinear": primary_code,
        "SW_UnitsLinearDecimalDisplay": FieldInt(length, "f10"),
        "SW_UnitsLinearDecimalPlaces": FieldInt(length, "f0c"),
        "SW_UnitsLinearFractionDenominator": FieldInt(length, "f28"),
        "SW_UnitsDualLinear": FieldInt(dual, "fb0"),
        "SW_UnitsTimeUnits": FieldInt(units["time"].FieldsValue, "fb0") + 1,
        "SW_UnitsPowerUnits": FieldInt(units["power"].FieldsValue, "fb0") + 1,
        "SW_UnitsEnergyUnits": FieldInt(units["energy"].FieldsValue, "fb0") + 1,
        "SW_UnitsDualLinearDecimalDisplay": FieldInt(dual, "f10"),
        "SW_UnitsDualLinearDecimalPlaces": FieldInt(dual, "f0c"),
        "SW_UnitsDualLinearFractionDenominator": FieldInt(dual, "f28"),
        "SW_UnitsAngular": FieldInt(angle, "fb0"),
        "SW_UnitsAngularDecimalPlaces": FieldInt(angle, "f0c"),
        "SW_UnitsMassPropLength": primary_code,
        "SW_UnitsMassPropDecimalPlaces": FieldInt(density, "f0c"),
        "SW_UnitsMassPropMass": FieldInt(density, "fc4") + 1,
        "SW_UnitsMassPropVolume": FieldInt(density, "fc0") + 1,
        "SW_UnitsTimeDecimalPlaces": FieldInt(units["time"].FieldsValue, "f0c"),
        "SW_UnitsForce": FieldInt(units["force"].FieldsValue, "fb0") + 1,
        "SW_UnitsForceDecimalPlaces": FieldInt(units["force"].FieldsValue, "f0c"),
        "SW_UnitsPowerDecimalPlaces": FieldInt(units["power"].FieldsValue, "f0c"),
        "SW_UnitsEnergyDecimalPlaces": FieldInt(units["energy"].FieldsValue, "f0c"),
        "SW_UnitsDecimalRounding": 0,
        "SW_UnitsLinearFeetAndInchesFormat": 1,
        "SW_UnitsLinearRoundToNearestFraction": 0,
        "SW_UnitsDualLinearRoundToNearestFraction": 0,
        "SW_UnitsDualLinearFeetAndInchesFormat": 1,
    }


def typed_values(values):
    if values.keys() != set(ASSEMBLY_NAMES):
        raise ValueError(
            "assembly information fields differ from the ordinary system table"
        )
    records = {}
    for pid, name in enumerate(ASSEMBLY_NAMES, 3):
        value = values[name]
        if 3 <= pid < 18 and type(value) is str and not KInvalidXml.search(value):
            records[pid] = name, "lpstr", value
        elif name == ASSEMBLY_KIND and value is False:
            records[pid] = name, "bool", "No"
        elif (
            pid >= 18
            and name != ASSEMBLY_KIND
            and type(value) is int
            and -(1 << 31) <= value < 1 << 31
        ):
            records[pid] = name, "i4", str(value)
        else:
            raise ValueError("unsupported ordinary assembly information field " + name)
    return records


def assembly_information(archive, output, offset_minutes):
    root = ReadNativeLink(archive, 0).ConfigValue.RootValue
    RequireNode(root, "moAssembly_c")
    fields = system_values(archive, root, output, offset_minutes) | unit_values(root)
    return EncodeInfoTable(typed_values(fields), ASSEMBLY_DICT_ORDER)


def add_assembly_information(streams, archive, output, offset_minutes):
    if KInfoXml in streams:
        raise ValueError("assembly information already has an owner")
    return streams | {KInfoXml: assembly_information(archive, output, offset_minutes)}
