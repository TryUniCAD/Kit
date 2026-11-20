from math import copysign, fsum, isclose, isfinite, sqrt

from para.concentric.CylinderFace import make_face, make_face_ref, make_facet, make_feature_file, node
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlacePoint import PlacePoint
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakePlacement import MakePlacement
from convert.adapters.solidworks.Archive.Construction.Assembly.RecordMateMut import RecordMateMut
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import FeatureTime
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Nodes.MakeAtomFeat import MakeAtomFeat
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import CompRefFields
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CopyPlacement import CopyPlacement
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeMateChain import MakeMateChain
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import SignedStamp
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, RequireNode


def xyz(values):
    return dict(zip("xyz", values, strict=True))


def dot(a, b):
    return fsum(x * y for x, y in zip(a, b, strict=True))


def world_axis(frame, axis):
    return tuple(dot(axis, column) for column in zip(frame.AxisU, frame.AxisV, frame.NormalValue, strict=True))


def selected_local_axes(carrier_axis, endpoint_axes):
    if endpoint_axes is None:
        return carrier_axis, carrier_axis
    if type(endpoint_axes) is not tuple or len(endpoint_axes) != 2:
        raise ValueError("concentric mate requires two ordered child-local axes")
    axes = []
    for axis in endpoint_axes:
        if type(axis) is not tuple or len(axis) != 3 or any(
            type(value) not in (int, float) or not isfinite(value) for value in axis
        ):
            raise ValueError("concentric child-local axis requires three finite scalars")
        sign = -1.0 if dot(axis, carrier_axis) < 0.0 else 1.0
        if not isclose(dot(axis, axis), 1.0, rel_tol=1e-10, abs_tol=1e-12) or not all(
            isclose(value, sign * carrier, rel_tol=1e-10, abs_tol=1e-12)
            for value, carrier in zip(axis, carrier_axis, strict=True)
        ):
            raise ValueError("concentric child-local axis must be a unit direction on the actual carrier")
        axes.append(tuple(float(value) for value in axis))
    if dot(*axes) <= 0.0:
        raise ValueError("concentric endpoint axes disagree on the same child cylinder")
    return tuple(axes)


def axial_bounds(face, frame, origin, axis, *, signed=False):
    distances = []
    for rim in face.rim_centres:
        difference = tuple(value - start for value, start in zip(PlacePoint(frame, rim), origin, strict=True))
        distance = dot(difference, axis)
        delta = tuple(distance * value for value in axis)
        distances.append(copysign(sqrt(dot(delta, delta)), distance))
    lower, upper = distances
    if lower != 0.0 or not isfinite(upper) or upper == 0.0 or (upper < 0.0 and not signed):
        raise ValueError("selected circular rims do not bound the ordinary rooted axial interval")
    return lower, upper


def make_wrapper(component, origin, axis, radius):
    return {
        "f58": component, "f60": None, "f68": 1, "f6c": 0, "f08": 101,
        "has_f10": 0, "has_f18": 0, "f0c": -1, "f20": 0,
        "f74": -12345, "f78": -12345, "f7c": -12345, "f50": 0,
        "f70": 19000, "f34": 0, "f30": 0, "f98": 0, "f38": -1,
        "fb0": -1.0, "fb8": 1.0, "fc0": 1.0, "fc8": -1.0,
        "fd0": xyz(origin), "fe8": xyz(axis), "f100": radius, "has_f108": 0,
    }


def make_active(parent, child, occurrence, pose, face, feature_file, origin, axis, local_axis, *, signed):
    chain = MakeMateChain(parent, occurrence)
    placement = occurrence.FieldsValue["f360"]
    stamp = child.HeaderValue.FieldsValue["f40"]
    component = node("moCompFace_c", {
        **CompRefFields(chain),
        "f18": occurrence.FieldsValue["f3f8"], "f1c": occurrence.FieldsValue["f3f8"],
        "alias": 0, "fe8": make_face_ref(face, feature_file), "ff0": None,
    })
    values = make_wrapper(component, origin, axis, face.radius)
    lower, upper = axial_bounds(face, pose, origin, axis, signed=signed)
    values.update(
        f08=SignedStamp(stamp), f0c=child.CurrentConfig.FieldsValue["f08"],
        has_f10=1, f10=CopyPlacement(placement), has_f18=1, f18=CopyPlacement(placement),
        f50=2, fb0=lower, fb8=upper, has_f108=1, f108=xyz(local_axis),
    )
    return node("moCylinderRef_w", values)


def make_support(state, header, target, occurrence, face, origin, axis):
    parent = state.RootValue
    root = RequireNode(parent.FieldsValue["f990"], "moUnitComponent_c")
    cylinder = MakeAtomFeat(parent, target).FieldsValue
    cylinder.update(f6c0=xyz((0.0, 0.0, 0.0)), f6dc=4, f6e0=0, f6e8=None, f6f0=0,
                    f6f8=xyz(origin), f710=xyz(axis), f728=face.radius)
    geometry = node("moRefCylinder_c", cylinder)
    component = node("moCompRefCylinder_c", {
        **CompRefFields(root),
        "ff0": {"f00": -1, "f08": DatumTime(header, -1)}, "ff8": geometry,
        "f90": face.body_atom, "f94": face.node_id,
        "has_fb0": 1, "fb0": make_facet(face),
        "has_fb8": 1, "fb8": ReadNodeName(occurrence) + "@" + ReadNodeName(parent),
        "has_fc8": 1, "fc8": CopyPlacement(occurrence.FieldsValue["f360"]),
    })
    fields = make_wrapper(component, origin, axis, face.radius)
    fields.update(f08=SignedStamp(header.FieldsValue["f40"]), f0c=state.CurrentConfig.FieldsValue["f08"])
    return node("moCylinderRef_w", fields)


def verify_placement(occurrence, pose, child):
    fields = occurrence.FieldsValue
    selected = fields["f3c0"]
    if (fields["f360"] != MakePlacement(pose)
            or fields["f3e0"] != child.HeaderValue.FieldsValue["f40"]
            or selected["f10"] != child.CurrentConfig.FieldsValue["f08"]
            or selected["f08"] != ReadNodeName(child.CurrentConfig)
            or ReadFileKey(fields["f3b0"]) != ReadFileKey(child.HeaderValue.FieldsValue["f38"])):
        raise ValueError("mate occurrence is outside the actual generated child and placement")


def valid_alignment(positions, directions, expected):
    first, second = directions
    displacement = tuple(b - a for a, b in zip(*positions, strict=True))
    length = dot(displacement, first)
    radial = tuple(value - length * normal for value, normal in zip(displacement, first, strict=True))
    return (isclose(dot(first, second), expected, rel_tol=1e-10, abs_tol=1e-12)
            and all(isclose(value, 0.0, abs_tol=1e-12) for value in radial))


def make_concentric(state, settings, headers, references, poses, attachment, name, alignment, lock, fixed, *, endpoint_axes=None):
    if (len(references) != 2 or references[0] is references[1] or len(poses) != 2
            or type(fixed) is not int or fixed not in (0, 1)
            or type(alignment) is not int or alignment not in (1, 2) or type(lock) is not bool):
        raise ValueError("concentric mate requires two actual occurrences, explicit alignment and one fixed anchor")
    parent = state.RootValue
    child = attachment.candidate
    for occurrence, pose in zip(references, poses, strict=True):
        verify_placement(occurrence, pose, child)
    face = make_face(attachment)
    local_axes = selected_local_axes(face.axis, endpoint_axes)
    positions = tuple(PlacePoint(pose, face.origin) for pose in poses)
    directions = tuple(world_axis(pose, axis) for pose, axis in zip(poses, local_axes, strict=True))
    if not valid_alignment(positions, directions, 1 if alignment == 1 else -1):
        raise ValueError("explicit prepositioned cylinder axes do not satisfy the selected alignment")
    shared = make_feature_file(child)
    active = [make_active(parent, child, occurrence, pose, face, shared, origin, axis, local_axis,
                          signed=endpoint_axes is not None)
              for occurrence, pose, origin, axis, local_axis in zip(references, poses, positions, directions, local_axes, strict=True)]
    support = [make_support(state, headers[0], settings.TargetValue, occurrence, face, origin, axis)
               for occurrence, origin, axis in zip(references, positions, directions, strict=True)]
    mate = node("moMateConcentric", {})
    InitFeatureMut(mate, name, state.GroupValue, settings.TargetValue)
    mate.FieldsValue["f35c"] = 0
    mate.FieldsValue.update(FeatureTime(settings.HeaderValue.CreatedAt))
    mate.FieldsValue.update(dict.fromkeys(("f388", "f390", "f394", "f3b8", "has_f3c0", "f438", "f480"), 0))
    mate.FieldsValue.update(dict.fromkeys(("f3c0", "f430", "f468", "f470", "f478")))
    mate.FieldsValue.update(
        f370=[], f3b4=alignment, f3c8=[{"k": i, "o": wrap} for i, wrap in enumerate(support)],
        f410=[{"o": wrap} for wrap in active], f448=[], f488="", f490="", f4b8=int(lock), f4c4=-1,
    )
    mate_id = state.Allocator.AllocateMut(mate)
    count = parent.FieldsValue["fd48"]
    for index, wrapper in enumerate(active):
        wrapper.FieldsValue.update(f74=mate_id, f78=count + index, f7c=index)
    parent.FieldsValue["fd48"] = count + len(active)
    references[fixed].FieldsValue["f408"] = 1
    RecordMateMut(state, settings, mate, headers)
    return mate
