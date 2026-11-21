from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginRef import MakeOriginRef
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import SignedStamp
from convert.adapters.solidworks.Archive.Construction.PlanarMates.WrapperFields import WrapperFields
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, RequireNode

from MakePatternPrincipalDisplay import point, put_principal_displays_mut
from PatternHingeGeometry import AXIS, ORIGIN


def wrapper(system, datum, axis, headers):
    reference = MakeOriginRef(datum, system.RootValue, axis)
    actual_id = FieldInt(datum.FieldsValue, "f08")
    creation = DatumTime(headers[0], actual_id)
    if DatumTime(headers[1], actual_id) != creation:
        raise ValueError("hinge support creation provenance disagrees across its own headers")
    reference.FieldsValue["ff0"]["f08"] = creation
    source = RequireNode(datum.FieldsValue["f6f8"], "moDefaultRefPlnData_c").FieldsValue
    fields = WrapperFields(reference)
    fields.update(f68=1, f08=SignedStamp(FieldInt(headers[0].FieldsValue, "f40")),
                  f0c=FieldInt(system.ConfigValues[0].FieldsValue, "f08"),
                  fd0=dict(source["root"]), fe8=dict(source["normal"]),
                  f100={**source["f20"], "f08": dict(source["f20"]["f08"])}, f188=point(ORIGIN))
    fields.update({key: source[f"b{i}"] for i, key in enumerate(("fb0", "fb8", "fc0", "fc8"))})
    return ArchiveNode(RuntimeClass("moPlaneRef_w", 1), fields)


def make_hinge_mut(system, settings, allocator, name, bounds):
    if len(system.ConfigValues) != 1 or system.ManagerValue.FieldsValue["f360"] is not system.ConfigValues[0]:
        raise ValueError("local finite hinge requires one actual active configuration")
    if any(ReadNodeName(node) == name for node in system.FeatureValues):
        raise ValueError("local finite hinge requires a distinct authored feature name")
    if type(name) is not str or not name or "\x00" in name:
        raise ValueError("expected an actual hinge name")
    displays = put_principal_displays_mut(system, bounds)
    top = displays["Top Plane"]
    _, _, center = top["display_root_m"]
    _, _, max_v, min_v = top["borders_m"]
    start_z, finish_z = center - min_v, center - max_v
    if not start_z > 0.0 > finish_z:
        raise ValueError("principal support must have an interior through-origin clipping interval")
    start, finish = (0.0, 0.0, start_z), (0.0, 0.0, finish_z)
    feature = ArchiveNode(RuntimeClass("moRefAxis_c", 1), {})
    InitFeatureMut(feature, name, system.RootValue, settings.TargetValue, allocator)
    feature.FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    feature.FieldsValue.update({key: [] for key in KAtomLists})
    feature.FieldsValue.update(f35c=0, f368={"n": 0, "items": []}, f388={"n": 0, "items": []},
                               f538=None, f4a0=1, f6c0=point(start), f6dc=4, f6e0=0, f6e8=None, f6f0=0)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    first, second = (wrapper(system, system.SystemValues.PlaneValues[axis], axis, headers) for axis in ("y", "x"))
    feature.FieldsValue["f700"] = ArchiveNode(RuntimeClass("moPlaneInterAxisData_c", 1), {
        "f18": point(start), "f30": point(finish), "f08": start_z, "f10": -finish_z,
        "f50": point(AXIS), "f68": point(ORIGIN), "f80": first, "f88": second,
    })
    return feature, headers
