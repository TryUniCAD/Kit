from datetime import date
import json

from AssemblyUnitTable import UNIT_STREAM, verify_unit_table
from ProjectD01Concentric import require
from ProveD01ConcentricBridge import REPO, fingerprint
from ProveConcentricSourceBrep import checked

from convert.adapters.solidworks.Archive.Construction.Units.MakeDualLength import MakeDualLength
from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitTable import MakeUnitTable
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.ParseDisplay import KInformationStream, KInformationTag, KIntegerTag
from convert.adapters.solidworks.Core.Properties.ReadPropRoot import ReadPropRoot
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Units.ReadPartUnitNodes import ReadUnitNodes


CASE_MANIFESTS = {
    "assemblies": ("e60ba221757cf1452d70d952eecc1eb41c75e2bc0711c0c6aac7c457f9cd15c8",
                   ("A0_one.SLDASM", "A1_two.SLDASM")),
    "assembly-synchronized": ("86729463bf5734f53e209de81f09976cc95bee8c7d33395eb512ec0ed8b823b3",
                              ("A13SyncedSingle.SLDASM", "A14SyncedRepeat.SLDASM")),
}
MASS_PROOF_SHA = "450595ed39d4a1a0adf08b758475832038b8a675873a60e193a5374559c160e6"
CODE_KEYS = (("unit_system", "fb0"), ("length", "fb0"), ("angle", "fb0"),
             ("force", "fb0"), ("density", "fc4"))
XML_CODES = ("SW_UnitSystem", "SW_UnitsLinear", "SW_UnitsAngular", "SW_UnitsForce",
             "SW_UnitsMassPropMass")
LOCALE_KEYS = ("SW-Short Date", "SW-Long Date")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December")


def unit_codes(units):
    return tuple(FieldInt(units[key].FieldsValue, member) for key, member in CODE_KEYS)


def observed_locale(short, long):
    month, day, year = (int(value) for value in short.split("/"))
    timestamp = date(year, month, day)
    require(long == f"{WEEKDAYS[timestamp.weekday()]}, {MONTHS[month - 1]} {day}, {year}",
            "system information uses a different short/long locale relationship")
    return timestamp.isoformat()


def xml_unit_evidence(archive, units):
    root = ReadPropRoot(archive.require(KInformationStream))
    require(root.tag == KInformationTag, "system information has a different typed property namespace")
    section, = (row for row in root if row.tag == "propertySection"
                and row.attrib.get("name") == "UserDefinedProperties")
    rows = {}
    for name in (*XML_CODES, *LOCALE_KEYS):
        item, = (row for row in section if row.tag == "property" and row.attrib.get("name") == name)
        require(len(item) == 1 and not len(item[0]), "system information unit property is not a scalar")
        rows[name] = item[0]
    text_tag = KIntegerTag.rsplit("}", 1)[0] + "}lpstr"
    require(all(rows[key].tag == KIntegerTag for key in XML_CODES)
            and all(rows[key].tag == text_tag and rows[key].text for key in LOCALE_KEYS),
            "system information has an unqualified preference or locale type")
    short, long = (rows[key].text for key in LOCALE_KEYS)
    lang = ReadHistMut(archive.require("_MO_VERSION_19000/History"), 19000).RootValue.FieldsValue["f38"]
    return {"archive_codes": unit_codes(units),
            "xml_codes": tuple(int(rows[key].text) for key in XML_CODES),
            "observed_date": observed_locale(short, long), "source_history_language": lang,
            "xml_bytes": len(archive.require(KInformationStream))}


def inspect_assembly(archive):
    root = ReadNativeLink(archive, 0).ConfigValue.RootValue
    payload = archive.require(UNIT_STREAM)
    units, counter = verify_unit_table(root, payload)
    return {**xml_unit_evidence(archive, units), "sha256": fingerprint(payload),
            "bytes": len(payload), "terminal_map": counter, "rows": len(units)}


def format_differences(root):
    native = ReadUnitNodes(root)
    require(unit_codes(native)[:3] == (4, 0, 0), "same-precision contrast requires disclosed MMGS display units")
    precision = FieldInt(native["length"].FieldsValue, "f0c")
    default = MakeUnitTable(UnitInput("mm", "degree", "mmgs", precision))
    projected = {}
    for (kind, actual), row in zip(native.items(), default.FieldsValue["items"], strict=True):
        new = row["o"].FieldsValue
        fields = actual.FieldsValue
        if kind == "density" and fields["has_fb8"] == 0:
            require(fields.get("fb8") is None, "empty density presence has a detached length object")
            fields = fields | {"fb8": None}
        if kind == "length":
            dual = fields["fb8"]
            expected = MakeDualLength("mm")
            require(dual is not None and dual is not actual and dual.ClassValue == expected.ClassValue
                    and dual.FieldsValue == expected.FieldsValue,
                    "the independently computed inch formatter differs from its actual source child")
        require(fields.keys() == new.keys(), "the source format has an unqualified additional owner")
        for key, value in fields.items():
            if value == new[key]:
                continue
            projected[f"{kind}.{key}"] = (["derived_dual_length", None] if kind == "length" and key == "fb8"
                                          else [value, new[key]])
    return projected


def assembly_controls():
    results = {}
    for folder, (pin, names) in CASE_MANIFESTS.items():
        root = REPO / "re/solidworks/v2026/corpus" / folder
        manifest = json.loads(checked(root / "Manifest.json", pin))
        entries = {row.get("file", row["name"]): row for row in manifest["records"]}
        for name in names:
            digest = entries[name]["sha256"]
            archive = SldprtArchive.from_bytes(checked(root / name, digest))
            results[name] = {"source_sha256": digest, **inspect_assembly(archive)}
    return results


def custom_preferences(disclosures):
    path = REPO / "re/solidworks/measurements/2026/DocumentMassUnitsNative01.json"
    receipt = json.loads(checked(path, MASS_PROOF_SHA))
    require(receipt["passed"] and receipt["heldout_inputs_read"] == 0 and receipt["writer_outputs"] == 0,
            "unit controls require their separately disclosed native source result")
    folder = disclosures / "DocumentMassUnitsOracle01/Inspection"
    results = {}
    for kind in ("center", "corner"):
        results[kind] = {}
        for mode in ("MillimeterGram", "CustomGram", "CustomKilogram"):
            pin = receipt["cases"][kind]["states"][mode]["sha256"]
            archive = SldprtArchive.from_bytes(checked(folder / kind / "Author" / (mode + ".SLDPRT"), pin))
            root = ReadNativeLink(archive, 0).ConfigValue.RootValue
            evidence = xml_unit_evidence(archive, ReadUnitNodes(root))
            system = "MMGS" if mode == "MillimeterGram" else "Custom"
            mass = "Kilograms" if mode == "CustomKilogram" else "Grams"
            native_system = receipt["native_api"]["unit_system"]["swUnitSystem_" + system]
            native_mass = receipt["native_api"]["mass"]["swUnitsMassPropMass_" + mass]
            require((evidence["xml_codes"][0], evidence["xml_codes"][-1]) == (native_system, native_mass),
                    "system XML values differ from the independent registered system or mass choices")
            results[kind][mode] = {"source_sha256": pin, **evidence}
    return results
