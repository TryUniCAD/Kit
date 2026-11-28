from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import os

from hole_source.ReadHoleApi import GUIDS, identity


METHODS = {
    "IFeatureManager": {
        "CreateDefinition", "CreateFeature", "InsertCutBlend", "InsertMultiFaceDraft",
        "InsertProtrusionBlend", "InsertProtrusionBlend2", "InsertRefPlane", "InsertRib",
    },
    "IFeature": {"GetDefinition", "GetErrorCode2", "GetTypeName2", "ModifyDefinition"},
    "ISelectionMgr": {
        "CreateSelectData", "GetSelectedObject6", "GetSelectedObjectCount2",
        "GetSelectedObjectMark", "GetSelectionPoint2", "SetSelectionPoint2",
    },
    "IModelDocExtension": {"GetPersistReference3", "SelectByID2"},
    "ISketchSegment": {"Select4"},
    "ISelectData": {"Mark", "X", "Y", "Z"},
    "IEntity": {"Select4"},
    "IFace2": {"Normal", "GetSurface"},
    "ILoftFeatureData": {
        "AccessSelections", "Centerline", "EndTangencyType", "GetProfileCount", "GuideCurveInfluence",
        "GuideCurves", "IsBossFeature", "IsThinFeature", "Merge", "PickPoints", "Profiles",
        "ReleaseSelectionAccess", "StartTangencyType",
    },
    "IRibFeatureData2": {
        "AccessSelections", "Body", "DraftAngle", "EnableDraft", "ExtrusionDirection", "FlipSide",
        "IsTwoSided", "RefSketchIndex", "ReleaseSelectionAccess", "ReverseThicknessDir", "Thickness",
    },
    "IDraftFeatureData2": {
        "AccessSelections", "Angle", "DirectionPull", "FacePropagation", "FacesToDraft", "GetDraftedEntities",
        "GetFacesToDraftCount", "NeutralPlane", "ReleaseSelectionAccess", "ReverseDirection", "Type",
    },
}

ENUMS = {
    "swDraftType_e": {"swNeutralPlaneDraft", "swPartingLineDraft", "swStepDraft"},
    "swFeatureNameID_e": {"swFmBlend", "swFmBlendCut", "swFmDraft"},
    "swObjectEquality": {"swObjectSame"},
    "swRefPlaneReferenceConstraints_e": {
        "swRefPlaneReferenceConstraint_Distance", "swRefPlaneReferenceConstraint_OptionFlip",
    },
    "swTangencyType_e": {"swTangencyNone"},
}


def inspect_methods(info, expected):
    rows = {}
    for index in range(info.GetTypeAttr().cFuncs):
        desc = info.GetFuncDesc(index)
        names = list(info.GetNames(desc.memid))
        if names and names[0] in expected:
            key = (names[0], desc.invkind)
            if key in rows:
                raise ValueError("duplicate installed dispatch binding")
            rows[key] = {
                "names": names, "member_id": desc.memid, "invocation_kind": desc.invkind,
                "arguments": repr(desc.args), "return_type": repr(desc.rettype),
            }
    if {name for name, _ in rows} != expected:
        raise ValueError("missing installed methods: " + ", ".join(sorted(expected - {name for name, _ in rows})))
    return [rows[key] for key in sorted(rows)]


def inspect_enum(info, expected):
    rows = {}
    for index in range(info.GetTypeAttr().cVars):
        desc = info.GetVarDesc(index)
        name = info.GetNames(desc.memid)[0]
        if type(desc.value) is int and name in expected:
            if name in rows:
                raise ValueError("duplicate installed enumeration value")
            rows[name] = desc.value
    if rows.keys() != expected:
        raise ValueError("missing installed enumerators: " + ", ".join(sorted(expected - rows.keys())))
    return rows


def capture():
    if os.name != "nt":
        raise ValueError("inspect the registered metadata in the installed Windows oracle")
    import pythoncom

    oracle = identity()
    methods, enums = {}, {}
    pythoncom.CoInitialize()
    try:
        for guid in GUIDS:
            library = pythoncom.LoadRegTypeLib(guid, 34, 0, 0)
            if tuple(library.GetLibAttr()[3:5]) != (34, 0):
                raise ValueError("registered source metadata must belong to release 34.0")
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                kind = info.GetTypeAttr().typekind
                if name in METHODS and kind in (pythoncom.TKIND_INTERFACE, pythoncom.TKIND_DISPATCH):
                    if name in methods:
                        raise ValueError("duplicate installed interface " + name)
                    methods[name] = inspect_methods(info, METHODS[name])
                if name in ENUMS and kind == pythoncom.TKIND_ENUM:
                    if name in enums:
                        raise ValueError("duplicate installed enumeration " + name)
                    enums[name] = inspect_enum(info, ENUMS[name])
    finally:
        pythoncom.CoUninitialize()
    if methods.keys() != METHODS.keys() or enums.keys() != ENUMS.keys():
        raise ValueError("the installed interface or enumeration roster differs")
    return {
        "schema": "kit.sw2026.loft-rib-draft-source-installation.v1", "executable": oracle,
        "libraries": ["34.0", "34.0"], "methods": methods, "enums": enums,
        "native_processes": 0, "native_files_authored": 0, "heldout_sources": 0,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    data = capture()
    raw = (json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"sha256": sha256(raw).hexdigest(), "bytes": len(raw), "native_processes": 0}))


if __name__ == "__main__":
    main()
