from ast import literal_eval
from hashlib import sha256
from itertools import product
from math import pi
import json

from ReadHoleApi import APP_HASH, encode

BASE = "e0d4349f18711d5ba9a04171c8a4b84d6e6603db"
BUILD = "34.5.2.0604"
API_SHA = "2819a07ed9096886bb54d8e6244b4da12d4a3560faf855292a300b447fd38784"
ORIGINAL_TOOL = "0c584b62ff17993500a7a18fa024f9eb72b0050d2dc4bddafe0b3ef9ae4f3a55"
CONTROL_PATH = "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"
CONTROL_SHA = "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"
HOLE = "WizardBore"
STOCK = "Stock"
PARAMETERS = (
    "GenericHoleType", "StandardIndex", "FastenerTypeIndex", "SSize", "EndType",
    "Diameter", "Depth", "Length", *(f"Value{i}" for i in range(1, 13)), "ThreadClass",
    "RevDir", "FeatureScope", "AutoSelect", "AssemblyFeatureScope", "AutoSelectComponents",
    "PropagateFeatureToParts",
)
ENUMS = {
    "swWzdGeneralHoleTypes_e": {"swWzdHole": 2, "swWzdCounterBore": 0},
    "swWzdHoleStandards_e": {"swStandardAnsiInch": 0, "swStandardISO": 8},
    "swWzdHoleStandardFastenerTypes_e": {"swStandardAnsiInchAllDrillSizes": 18, "swStandardISOHexCapScrew": 136},
    "swWzdHoleTypes_e": {"swHoleThru": 25, "swCounterBoreThru": 14},
    "swWzdHoleScrewClearanceTypes_e": {"swScrewClearanceNormal": 1},
}
PROPERTIES = {"Type": (4, 22), "Diameter": (5, 5), "CounterBoreDiameter": (6, 5),
              "HoleDiameter": (11, 5), "ThruHoleDiameter": (12, 5), "CounterBoreDepth": (20, 5),
              "EndCondition": (39, 22), "FastenerSize": (42, 8), "ReverseDirection": (56, 11),
              "Standard2": (64, 3), "FastenerType2": (65, 3)}
OPERATIONS = {"AccessSelections": (1, (9, 9), 11), "ReleaseSelectionAccess": (3, (), 24),
              "GetSketchPointCount": (47, (), 3), "GetSketchPoints": (48, (), 12)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def checked(path, pin):
    require(path.is_file() and not path.is_symlink(), "expected pinned input file")
    raw = path.read_bytes()
    require(digest(raw) == pin, "pinned input changed: " + path.name)
    return raw


def exact_member(report, owner, name, kind, member_id, argument_types, return_type):
    (row,) = (row for row in report["methods"][owner]
              if row["invocation_kind"] == kind and row["names"][0] == name)
    require(row["member_id"] == member_id
            and literal_eval(row["arguments"]) == tuple((value, 1, None) for value in argument_types)
            and literal_eval(row["return_type"]) == (return_type, 0, None),
            "installed argument type, invocation or return binding differs at " + name)
    return row


def installation(raw):
    require(digest(raw) == API_SHA, "root-captured installed metadata digest differs")
    report = json.loads(raw)
    require(raw == encode(report)
            and report["schema"] == "kit.sw2026.hole-source-installation.v1"
            and report["executable"] == {"file_version": BUILD, "prog_id": "SldWorks.Application.34", "sha256": APP_HASH}
            and report["libraries"] == ["34.0", "34.0"]
            and report["native_processes"] == report["native_files_authored"] == report["heldout_sources"] == 0,
            "wrong exact-build metadata provenance")
    require(all(report["enums"][group].get(key) == value for group, rows in ENUMS.items()
                for key, value in rows.items()), "used installed hole catalog or type enum differs")
    call = exact_member(report, "IFeatureManager", "HoleWizard5", 1, 222,
                        (3, 3, 3, 8, 2, *(5,) * 15, 8, *(11,) * 6), (26, (29, 50337536)))
    require(call["names"][1:] == list(PARAMETERS), "installed HoleWizard5 argument order differs")
    selected = [exact_member(report, "IWizardHoleFeatureData2", name, 2, member_id, (), result)
                for name, (member_id, result) in PROPERTIES.items()]
    selected.extend(exact_member(report, "IWizardHoleFeatureData2", name, 1, mid, arg, result)
                    for name, (mid, arg, result) in OPERATIONS.items())
    selected.extend(exact_member(report, "IWizardHoleFeatureData2", name, 4, PROPERTIES[name][0], (5,), 24)
                    for name in ("HoleDiameter", "CounterBoreDepth"))
    return report, call, selected


def cases():
    return (
        {"name": "PlainThrough", "cohort": "disclosed", "stock_m": [0.07813, 0.04917, 0.02531],
         "at_m": [0.02173, 0.03087], "diameter_m": 0.00637, "upper_m": 0.0, "step_m": 0.0,
         "catalog": [2, 0, 18, "#97"], "observed_type": 25, "edit_property": "HoleDiameter", "edit_m": 0.00811},
        {"name": "CounterboreThrough", "cohort": "disclosed", "stock_m": [0.09815, 0.07139, 0.02141],
         "at_m": [0.06137, 0.02473], "diameter_m": 0.0066, "upper_m": 0.01371, "step_m": 0.00373,
         "catalog": [0, 8, 136, "M6"], "observed_type": 14, "edit_property": "CounterBoreDepth", "edit_m": 0.00519},
    )


def arguments(case):
    values = ([case["upper_m"], case["step_m"], 0.0] if case["upper_m"] else [-1.0] * 3) + [-1.0] * 9
    args = (*case["catalog"], 1, case["diameter_m"], case["stock_m"][2], -1.0,
            *values, "", False, False, False, False, False, False)
    require(len(args) == len(PARAMETERS), "Hole Wizard argument assembly lost a formal slot")
    return args


def estimate(case, edited=False):
    width, height, thick = case["stock_m"]
    x, y = case["at_m"]
    radius = (case["edit_m"] if edited and case["edit_property"] == "HoleDiameter" else case["diameter_m"]) / 2
    upper = case["upper_m"] / 2
    step = case["edit_m"] if edited and case["edit_property"] == "CounterBoreDepth" else case["step_m"]
    largest = max(radius, upper)
    require(0 < largest < min(x, y, width - x, height - y)
            and (upper == step == 0 or upper > radius and 0 < step < thick),
            "hole or counterbore does not fit its authored slab")
    volume0 = width * height * thick
    bore = pi * radius**2 * thick
    annulus = pi * (upper**2 - radius**2) * step if step else 0.0
    volume = volume0 - bore - annulus
    center = ((volume0 * width / 2 - (bore + annulus) * x) / volume,
              (volume0 * height / 2 - (bore + annulus) * y) / volume,
              ((volume0 - bore) * thick / 2 - annulus * (thick - step / 2)) / volume)
    area = (2 * (width * height + width * thick + height * thick) - 2 * pi * radius**2
            + 2 * pi * (radius * (thick - step) + upper * step))
    return {
        "volume_m3": volume, "area_m2": area, "centroid_m": center, "body_count": 1,
        "point_m": (x, y, thick), "cylinder_radii_m": (radius, upper) if step else (radius,),
        "minimum_m": (0.0, 0.0, 0.0), "maximum_m": (width, height, thick),
        "fixed_stock_corners_m": tuple(product((0.0, width), (0.0, height), (0.0, thick))),
        "hole_diameter_m": radius * 2, "counterbore_depth_m": step, "counterbore_diameter_m": upper * 2,
    }


def packet_model():
    return {"cohort": "disclosed",
            "jobs": tuple({"case": case, "call": dict(zip(PARAMETERS, arguments(case), strict=True)),
                           "original": estimate(case), "edited": estimate(case, True)}
                          for case in cases())}
