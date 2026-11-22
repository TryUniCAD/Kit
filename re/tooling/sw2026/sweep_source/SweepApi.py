from FilletApi import CONSTS_LIB, MODEL_LIB, load
from SweepModel import require

SWEEP_OPTIONS = {
    "CircularProfile": False,
    "ThinFeature": False,
    "TwistControlType": "swTwistControlFollowPath",
    "PathAlignmentType": "swTangencyNone",
    "StartTangencyType": "swTangencyNone",
    "EndTangencyType": "swTangencyNone",
    "AlignWithEndFaces": False,
    "TangentPropagation": False,
    "MaintainTangency": False,
    "AdvancedSmoothing": False,
    "Merge": True,
    "FeatureScope": True,
    "AutoSelect": True,
}
ENUMS = {
    "swFeatureNameID_e": ("swFmSweep",),
    "swConstraintType_e": ("swConstraintType_FIXED", "swConstraintType_HORIZPOINTS", "swConstraintType_VERTPOINTS",
                           "swConstraintType_DIAMETER", "swConstraintType_RADIUS"),
    "swSketchRelationEntityTypes_e": ("swSketchRelationEntityType_Arc",),
    "swSketchRelationFilterType_e": ("swAll", "swDangling", "swOverDefining", "swBroken"),
    "swSelectType_e": ("swSelSKETCHES", "swSelDATUMPLANES"),
    "swSketchSegments_e": ("swSketchARC",),
    "swObjectEquality": ("swObjectSame",),
    "swTwistControlType_e": ("swTwistControlFollowPath",),
    "swTangencyType_e": ("swTangencyNone",),
    "swMassPropertyAccuracyLevel_e": ("swMassPropertyAccuracyLevel_Higher",),
    "swBodyType_e": ("swSolidBody", "swSheetBody"),
    "swDimensionType_e": ("swRadialDimension", "swDiameterDimension"),
    "swDimensionDrivenState_e": ("swDimensionDriving",),
    "swSetValueInConfiguration_e": ("swSetValue_InThisConfiguration",),
    "swSetValueReturnStatus_e": ("swSetValue_Successful",),
    "swUserPreferenceToggle_e": ("swDisplayFeatureDimensions", "swInputDimValOnCreate"),
    "swUserPreferenceDoubleValue_e": ("swMaterialPropertyDensity",),
    "swUserPreferenceOption_e": ("swDetailingNoOptionSpecified",),
}
MEMBERS = {
    "ISldWorks": ("IsSame",),
    "IFeatureManager": ("CreateDefinition", "CreateFeature"),
    "ISweepFeatureData": (*SWEEP_OPTIONS, "Direction", "SweepType", "GetGuideCurvesCount", "IsBossFeature", "IsThinFeature",
                          "GetProfileType", "GetPathType", "Profile", "Path", "AccessSelections", "ReleaseSelectionAccess"),
    "ISketchManager": ("InsertSketch", "ActiveSketch", "AddToDB", "CreateCircleByRadius", "CreateArc"),
    "ISketch": ("GetConstrainedStatus", "GetSketchSegments", "ModelToSketchTransform", "RelationManager",
                "GetReferenceEntity"),
    "ISketchArc": ("IsCircle", "GetRadius", "GetCenterPoint2", "GetStartPoint2", "GetEndPoint2", "GetRotationDir"),
    "ISketchRelation": ("GetRelationType", "GetEntities", "GetEntitiesType", "GetEntitiesCount", "Suppressed"),
    "ISketchRelationManager": ("AddRelation", "GetRelations", "GetRelationsCount"),
    "IModelDoc2": ("AddRadialDimension2", "AddDiameterDimension2", "ForceRebuild3"),
    "IModelDocExtension": ("SelectByID2", "SetUserPreferenceDouble", "GetUserPreferenceDouble",
                           "CreateMassProperty", "CreateMassProperty2"),
    "IMassProperty2": ("AccuracyLevel", "UseSystemUnits", "SelectedItems", "Recalculate",
                       "GetOverrideOptions", "Volume", "SurfaceArea", "CenterOfMass", "Mass"),
    "IMassPropertyOverrideOptions": ("OverrideMass", "OverrideCenterOfMass"),
    "IDimension": ("FullName", "SystemValue", "SetSystemValue3", "DrivenState", "ReadOnly"),
    "IDisplayDimension": ("Type2", "GetDimension2"),
    "ISelectionMgr": ("GetSelectedObject6", "GetSelectedObjectCount2", "GetSelectedObjectType3"),
    "IFeature": ("GetParents", "GetDefinition", "GetSpecificFeature2", "GetFirstDisplayDimension", "GetNextDisplayDimension"),
    "IBody2": ("GetFaces", "GetEdges", "GetVertices", "GetExtremePoint", "GetType", "Select2"),
    "IFace2": ("GetSurface", "GetFeature", "GetArea"),
    "ISurface": ("IsPlane", "IsTorus"),
}


def inspect_registration(sw):
    model, model_id = load(sw, MODEL_LIB)
    types = {model.GetDocumentation(index)[0]: index for index in range(model.GetTypeInfoCount())}
    interfaces = {}
    for name, names in MEMBERS.items():
        require(name in types, f"registered interface is unavailable: {name}")
        info = model.GetTypeInfo(types[name])
        signatures = {}
        for offset in range(info.GetTypeAttr().cFuncs):
            member = info.GetFuncDesc(offset)
            arguments = info.GetNames(member.memid)
            if arguments and arguments[0] in names:
                signatures.setdefault(arguments[0], []).append({
                    "member_id": member.memid, "invoke_kind": member.invkind,
                    "names": list(arguments), "arguments": repr(member.args), "return": repr(member.rettype),
                })
        require(set(signatures) == set(names), f"registered {name} lacks members {sorted(set(names) - signatures.keys())}")
        interfaces[name] = signatures
    const, const_id = load(sw, CONSTS_LIB)
    types = {const.GetDocumentation(index)[0]: index for index in range(const.GetTypeInfoCount())}
    constants = {}
    for enum, names in ENUMS.items():
        require(enum in types, f"registered enum is unavailable: {enum}")
        info = const.GetTypeInfo(types[enum])
        entries = [info.GetVarDesc(index) for index in range(info.GetTypeAttr().cVars)]
        values = {info.GetNames(entry.memid)[0]: entry.value for entry in entries}
        require(all(type(values.get(name)) is int for name in names), f"registered {enum} lacks expected members")
        constants.update({name: values[name] for name in names})
    return constants, {"model_library": model_id, "constants_library": const_id,
                       "interfaces": interfaces, "constants": constants}


def options(constants):
    return {name: constants[value] if isinstance(value, str) else value for name, value in SWEEP_OPTIONS.items()}
