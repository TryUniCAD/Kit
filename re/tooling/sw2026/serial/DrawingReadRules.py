from __future__ import annotations

from CheckDrawingPrefix import concept_registry
from ReadRuleExpressions import UnportableExpression, compile_callable, constant, literal
from Schema import Base, Cnt, Emb, Fn, If, O, P, Raw, Rep, S
from defs.CommonPartOwners2026 import require_common_part_version
from defs.ConfigAssembly import Counted, Version2026, WithCondition
from defs.ConfigPart import Direct, Norm, ObjIf, Present
from defs.ConfigUnits import HasObj
from defs.MaterialDisplay import require_display_context
from defs.ResolvedCore import OIf, VIf, VT, Virt, XO


VERSION = 19000
OBJECT_CLASSES = (
    "moAbsoluteRefPlnData_c", "moAbsoluteView", "moAngleUserUnits_c", "moBlockFolder_c",
    "moCStringHandle_c", "moChainComponent_c", "moCommentsFolder_c", "moCompProfile_c",
    "moCompRefPlane_c", "moDensityUnits_c", "moDetailCabinet_c", "moDetailFolder_c",
    "moDisplayProfileFeature_c", "moDocsFolder_c", "moDrSheet", "moDrawingRefPlnData_c",
    "moDrawing_c", "moEnergyUnits_c", "moExtFeatureList_c", "moExtFeature_c",
    "moExtObjectList_c", "moExtObject_c", "moFloatNumberUserUnits_c", "moForceUnits_c",
    "moFrequencyUserUnits_c", "moGravityUnits_c", "moHeader_c", "moInkMarkupFolder_c",
    "moLengthUserUnits_c", "moLinearMotorUnits_c", "moLogs_c", "moMarkupCommentFolder_c",
    "moNodeName_c", "moNumberUserUnits_c", "moPowerUnits_c", "moProfileFeature_c",
    "moRefPlane_c", "moReferenceChain_c", "moReferenceInternal_c", "moRotaryMotorUnits_c",
    "moScaleSysScale_c", "moSpringConstantUnits_c", "moStamp_c", "moStressUnits_c",
    "moTimeUnits_c", "moTransRefPlaneData_c", "moUnitComponent_c", "moUnitSysUnits_c",
    "moUnitsTable_c", "sgSketch", "suObList",
)
CLASS_SCHEMAS = {**dict.fromkeys(OBJECT_CLASSES, 1), "su_CStringArray": 0}
METHODS = tuple("""
FUN_4bb09f20
mgBBox_c.restore
mgPoint_c.restore
mgVector_c.restore
mgXform_c.restore
moAbsoluteRefPlnData_c
moAbsoluteView
moAngleUserUnits_c
moAtomFeature_c
moBlockFolder_c
moCStringHandle_c
moChainComponent_c
moCommentsFolder_c
moCompFeature_c
moCompProfile_c
moCompRefPlane_c
moCompRef_c
moComponent_c
moConcept_c.SerializeLWData
moConcept_c.SerializeResolvedData
moDensityUnits_c
moDetailCabinet_c
moDetailFolder_c
moDetailFolder_c.SerializeXmlData
moDisplayObject_c.FUN_4ba4d3c0
moDisplayProfileFeature_c
moDocsFolder_c
moDrSheet
moDrSheet.SerializeXmlData
moDrView
moDrView.Archive
moDrView.SerializeXmlData
moDrawingRefPlnData_c
moDrawing_c
moEnergyUnits_c
moEntVisProp_c
moExtFeatureList_c
moExtFeature_c
moExtObjectInterface_c.FUN_4c179410
moExtObjectList_c
moExtObject_c
moFRData_c
moFeature_c
moFeature_c.FUN_4bb2b240
moFeature_c.SerializeXmlData
moFloatNumberUserUnits_c
moFolder_c
moForceUnits_c
moFrequencyUserUnits_c
moGravityUnits_c
moHeader_c
moInkMarkupFolder_c
moLengthUserUnits_c
moLineViz_c.Serialize.0
moLinearMotorUnits_c
moLogs_c
moMarkupCommentFolder_c
moModelFeature_c
moModel_c.FUN_4c17aa00
moModel_c.FUN_4c216d80
moModel_c.FUN_4c22ec20
moModel_c.FUN_4c22ec80
moNodeList_c.Serialize
moNodeName_c
moNode_c.SerializeLWData
moNode_c.SerializeNode
moNumberUserUnits_c
moPowerUnits_c
moProfileData.FUN_4bb2ca30
moProfileData.FUN_4bb2d5c0
moProfileFeature_c
moProfileFeature_c.FUN_4bb2d1d0
moProfileFeature_c.contours
moRefGeom_c
moRefPlane_c
moRefPlane_c.SerializeXmlData
moRefPlnData_c.serializePlaneData
moReferenceChain_c
moReferenceInternal_c
moReference_c
moReferencedConfiguration_c
moRotaryMotorUnits_c
moScaleSysScale_c
moSharedFileDef_c
moSpringConstantUnits_c
moStamp_c
moStressUnits_c
moTimeUnits_c
moTransRefPlaneData_c
moUnitComponent_c
moUnitSysUnits_c
moUnitsTable_c
moUserUnits_c.Serialize
moVisProp_c
mo_loadBodyFromArchive
rf.suObArray
rf.suObList
rf.su_CMapObToInt
sgSketch
sk.EquationVarValueMap_c.FUN_4c339ca0
sk.moSketchRelMgr_c.FUN_4c6035c0
sk.pnt3DcoincMap_c.FUN_4b9611e0
sk.sgBlockManager.FUN_4c90b810
sk.sgCreationIDs.FUN_4c5864f0
sk.sgEntHandleDataManager_c.FUN_4c90bf80
sk.sgLoopManager.FUN_4c58cf30
sk.sgSketch.FUN_4c5a0f00
sk.sgSlotManager_c.FUN_4c59a5f0
suObList
su_CMapStringToOb.Serialize
su_CObArray
su_CStringArray
utLineWidth_c.Serialize.3.0
utLineWidth_c.Serialize2
viewSketchCache
""".split())
SCOPE = ("scope",)
ARCHIVE = ("archive",)
CONTEXT = ("context",)
NODE = ("node",)
CLASS = ("class_name",)


def call(function, *arguments):
    return constant(compile_callable(function, arguments, VERSION))


def select(condition, on_true, on_false):
    if condition[0] == "literal":
        return on_true() if condition[1] else on_false()
    return (("if", condition, on_true(), on_false()),)


def slot_methods(slot):
    return {name: target for name, target in VT[slot].items() if name in CLASS_SCHEMAS}


def compile_operation(operation):
    match operation:
        case P():
            return (("scalar", operation.name, operation.kind),)
        case S():
            return (("text", operation.name),)
        case Cnt():
            return (("count", operation.name),)
        case O() | XO():
            return (("object", operation.name),)
        case Base():
            return (("base", operation.cls),)
        case Emb():
            return (("embedded", operation.name, operation.cls),)
        case Raw():
            if callable(operation.n):
                width = call(operation.n, SCOPE, ARCHIVE)
            else:
                width = literal(operation.n)
            return (("fixed_bytes", operation.name, width),)
        case Rep():
            count = call(operation.count, SCOPE, ARCHIVE) if callable(operation.count) else ("lookup", SCOPE, literal(operation.count))
            return (("repeat", operation.name, count, compile_operations(operation.body)),)
        case If():
            return select(call(operation.pred, SCOPE, ARCHIVE), lambda: compile_operations(operation.then), lambda: compile_operations(operation.other))
        case OIf():
            return select(call(operation.pred, NODE), lambda: compile_operations(operation.then), lambda: compile_operations(operation.other))
        case VIf():
            classes = tuple(sorted(name for name, target in slot_methods(operation.slot).items() if target))
            expected = tuple(sorted(slot_methods(operation.slot)))
            return (("if_virtual", expected, classes, compile_operations(operation.then)),)
        case Virt():
            rows = tuple(sorted(slot_methods(operation.slot).items()))
            return (("virtual", rows),)
        case Version2026():
            return ()
        case Direct():
            return (("inline_header",),)
        case ObjIf() | HasObj():
            kind = operation.kind if isinstance(operation, ObjIf) else "u8"
            return (("present", operation.flag, kind, (("object", operation.field),)),)
        case Present():
            return (("present", operation.flag, operation.kind, compile_operations(operation.body)),)
        case Counted():
            return (("counted", operation.name, operation.kind, compile_operations(operation.body)),)
        case Norm():
            return (("normalize", operation.name, operation.kind, call(operation.fn, ("wire",), ARCHIVE)),)
        case WithCondition():
            return (("condition", operation.mask, compile_operations(operation.body)),)
        case Fn() if operation.fload is require_common_part_version:
            return ()
        case Fn() if operation.fload is require_display_context:
            return (("exclude_conditions", 0x10000001),)
        case _:
            return (("reject", f"{type(operation).__module__}.{type(operation).__name__}"),)


def compile_operations(operations):
    result = []
    for operation in operations:
        try:
            result.extend(compile_operation(operation))
        except UnportableExpression as error:
            result.append(("reject", str(error)))
    return tuple(result)


def compile_methods():
    registry = concept_registry()
    if set(CLASS_SCHEMAS) - set(METHODS):
        raise ValueError("drawing concept lies outside the admitted class methods")
    return {name: compile_operations(registry.classes[name]) for name in METHODS}
