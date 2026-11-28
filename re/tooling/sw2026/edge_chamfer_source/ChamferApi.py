from FilletApi import CONSTS_LIB, MODEL_LIB, load
from FilletModel import require

INTERFACES = {
    "IFeatureManager": {"FeatureExtrusion3": 23, "InsertFeatureChamfer": 8},
    "IChamferFeatureData2": {"Type": 0, "TangentPropagation": 0, "KeepFeatures": 0,
                            "PropagateFeatureToParts": 0, "Edges": 0, "Faces": 0, "Loops": 0, "Vertex": 0,
                            "GetEdgeCount": 0, "GetFaceCount": 0, "LoopCount": 0, "GetIsFlipped": 1,
                            "EdgeChamferAngle": 0, "GetEdgeChamferDistance": 1,
                            "AccessSelections": 2, "ReleaseSelectionAccess": 0},
    "ISelectionMgr": {"GetSelectedObject6": 2, "GetSelectedObjectCount2": 1, "GetSelectedObjectType3": 2,
                      "CreateSelectData": 0},
    "IEntity": {"Select4": 2},
    "IDisplayDimension": {"GetDimension2": 1, "Type2": 0},
    "IDimension": {"SystemValue": 0, "FullName": 0, "ReadOnly": 0, "DrivenState": 0, "SetSystemValue3": 3},
    "IFeature": {"GetDefinition": 0, "GetTypeName2": 0, "GetFirstDisplayDimension": 0,
                 "GetNextDisplayDimension": 1, "GetParents": 0, "GetFaces": 0},
    "ISelectData": {"Mark": 0},
    "IBody2": {"GetFaces": 0, "GetEdges": 0, "GetVertices": 0, "GetExtremePoint": 6},
    "IEdge": {"GetStartVertex": 0, "GetEndVertex": 0, "GetCurve": 0, "GetTwoAdjacentFaces2": 0},
    "IFace2": {"GetArea": 0, "GetFeature": 0, "GetSurface": 0, "GetEdges": 0, "GetBody": 0},
}
ENUMS = {
    "swChamferType_e": {"swChamferAngleDistance": 1},
    "swFeatureChamferOption_e": {"swFeatureChamferFlipDirection": 1, "swFeatureChamferKeepFeature": 2,
                                 "swFeatureChamferTangentPropagation": 4, "swFeatureChamferPropagateFeatToParts": 8},
    "swSelectType_e": {"swSelEDGES": 1},
    "swBodyType_e": {"swSolidBody": 0, "swSheetBody": 1},
    "swEndConditions_e": {"swEndCondBlind": 0},
    "swDimensionType_e": {"swChamferDimension": 10},
    "swDimensionDrivenState_e": {"swDimensionDriving": 2},
    "swSetValueInConfiguration_e": {"swSetValue_InThisConfiguration": 1},
    "swSetValueReturnStatus_e": {"swSetValue_Successful": 0},
    "swObjectEquality": {"swObjectSame": None},
    "swUserPreferenceToggle_e": {"swDisplayFeatureDimensions": None},
}


def installed_api(sw, *, distance_pair=False):
    model, model_id = load(sw, MODEL_LIB)
    consts, constants_id = load(sw, CONSTS_LIB)
    interfaces, enums, constants = {}, {}, {}
    expected_interfaces = INTERFACES
    expected_enums = ENUMS
    if distance_pair:
        expected_interfaces = INTERFACES | {
            "IChamferFeatureData2": INTERFACES["IChamferFeatureData2"] | {"EqualDistance": 0},
        }
        expected_enums = ENUMS | {
            "swChamferType_e": ENUMS["swChamferType_e"] | {
                "swChamferDistanceDistance": 2,
                "swChamferEqualDistance": 16,
            },
        }
    for index in range(model.GetTypeInfoCount()):
        name = model.GetDocumentation(index)[0]
        if name not in expected_interfaces:
            continue
        info = model.GetTypeInfo(index)
        observed = {}
        for offset in range(info.GetTypeAttr().cFuncs):
            member = info.GetFuncDesc(offset)
            names = info.GetNames(member.memid)
            if not names or names[0] not in expected_interfaces[name]:
                continue
            if member.invkind not in (sw.pythoncom.INVOKE_FUNC, sw.pythoncom.INVOKE_PROPERTYGET):
                continue
            nargs = len(member.args)
            require(nargs == expected_interfaces[name][names[0]], f"registered {name}.{names[0]} arity differs: {nargs}")
            if name == "IFeatureManager" and names[0] == "InsertFeatureChamfer":
                require(tuple(arg[0] for arg in member.args) == (3, 3, 5, 5, 5, 5, 5, 5),
                        "registered InsertFeatureChamfer argument types differ from two I4 and six R8")
            if name == "IChamferFeatureData2" and names[0] == "GetIsFlipped":
                require(member.memid == 26 and member.invkind == sw.pythoncom.INVOKE_FUNC
                        and list(names) == ["GetIsFlipped", "Entity"] and member.args == ((9, 1, None),)
                        and member.rettype == (11, 0, None),
                        "registered GetIsFlipped requires the actual entity and a Boolean result")
            observed[names[0]] = {"id": member.memid, "invoke_kind": member.invkind, "names": list(names),
                                  "arguments": repr(member.args), "result": repr(member.rettype)}
        require(observed.keys() == expected_interfaces[name].keys(), f"unbound {name} members: {expected_interfaces[name].keys() - observed.keys()}")
        interfaces[name] = observed
    require(interfaces.keys() == expected_interfaces.keys(), "registered 34.0 chamfer interfaces are incomplete")
    for index in range(consts.GetTypeInfoCount()):
        name = consts.GetDocumentation(index)[0]
        if name not in expected_enums:
            continue
        info = consts.GetTypeInfo(index)
        values = {info.GetNames(member.memid)[0]: member.value
                  for member in (info.GetVarDesc(offset) for offset in range(info.GetTypeAttr().cVars))}
        for key, expected in expected_enums[name].items():
            value = values.get(key)
            require(type(value) is int and (expected is None or value == expected), f"registered {name}.{key} differs")
            constants[key] = value
        enums[name] = {key: constants[key] for key in expected_enums[name]}
    require(enums.keys() == expected_enums.keys(), "registered 34.0 chamfer enums are incomplete")
    return constants, {"model_library": model_id, "constants_library": constants_id,
                       "interfaces": interfaces, "constants": enums}
