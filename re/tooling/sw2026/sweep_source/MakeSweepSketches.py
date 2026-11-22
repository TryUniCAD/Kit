from dataclasses import dataclass
from math import isfinite

from convert.adapters.solidworks.Archive.Construction.Circles.AddCircDimMut import AddCircDimMut
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import CircleInput
from convert.adapters.solidworks.Archive.Construction.Circles.MakeArcHandle import MakeArcHandle
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircleFeat import MakeCircleFeat
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import DimensionGraph
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginFix import MakeOriginFix
from convert.adapters.solidworks.Archive.Construction.Profile.BeginProfileMut import BeginProfileMut
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileData import MakeProfileData
from convert.adapters.solidworks.Archive.Construction.Sketch.EntityFields import EntityFields
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import MakeRingPoint
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import MakeSketchSeed
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeBinaryDim import MakeBinaryDim
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakePointRef import MakePointRef
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RequireDimRows import RequireDimRows
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from MakeSweepPathDim import make_path_dimension
from SweepModel import PATH, SECTION, require


@dataclass(frozen=True)
class SweepProfiles:
    section: ArchiveNode
    path: ArchiveNode
    section_d1: DimensionGraph
    path_d1: DimensionGraph


def need_radii(section_radius, path_radius):
    require(all(type(radius) in (int, float) and isfinite(radius) for radius in (section_radius, path_radius))
            and 0.001 <= section_radius < path_radius <= 0.15, "need positive separated quarter-tube radii")


def make_path_arc(sketch, radius):
    start = MakeRingPoint(sketch, (0.0, 0.0), 0)
    end = MakeRingPoint(sketch, (radius, radius), 1)
    center = MakeRingPoint(sketch, (0.0, radius), 2)
    points = center, start, end
    fields = EntityFields(sketch)
    fields.update({
        "_center": center, "_start": start, "_end": end, "f08": 1, "f0c": 1,
        "fd4": 0, "seg_tol": -1.0, "fd8": 1, "fe0": -2, "fe4": -2, "fe8": -2, "fec": -2,
    })
    for key, point in (("fc8", start), ("fcc", end), ("fdc", center)):
        fields[key] = fields[key + "_s"] = points.index(point)
    arc = ArchiveNode(RuntimeClass("sgArc", 1), fields)
    for point in points:
        point.FieldsValue.update(fe8=1, fec=int(point is center))
        if point is not center:
            point.FieldsValue["h1"] = MakeArcHandle(sketch, arc, 0)
    fields["fd0"] = int(all(point.FieldsValue["h1"].FieldsValue["_arc"] is arc for point in (start, end)))
    sketch.FieldsValue.update(
        points=tuple({"kind": 0, "point": point.FieldsValue} for point in points),
        arcs=({"flags": 0, "arc": fields},), npoints=len(points), narcs=1, f130=2, f56c=2,
    )
    sketch.FieldsValue["f140"].update(f08=len(points) + 1, f10=sketch.FieldsValue["narcs"] + 1)
    return arc, points


def publish_path_dim(sketch, arc, points, dimension):
    center, start, end = points
    dimensions = RequireDimRows(sketch)
    point_refs = tuple(MakePointRef(sketch, points, point) for point in points)
    fixed = MakeOriginFix(sketch, start)
    fixed.FieldsValue["h1"] = point_refs[1]
    vertical = MakeBinaryDim(sketch, 26, point_refs[0], MakePointRef(sketch, points, start))
    horizontal = MakeBinaryDim(sketch, 25, point_refs[2], MakePointRef(sketch, points, center))
    fixed_rows = ({"d": fixed.FieldsValue},)
    pair_rows = tuple({"d": relation} for relation in (vertical, horizontal))
    values = ({"d": dimension.DimensionValue},)
    displays = ({"o": dimension.DisplayValue},)
    dimensions.update(nlog1=len(fixed_rows), log_g1=fixed_rows, nlog2=len(pair_rows), log_g2=pair_rows,
                      ng1=len(values), val_g1=values)
    dimensions["f118"].FieldsValue.update(n=len(displays), items=displays)
    for point in points:
        point.FieldsValue["f20"] = sum(
            handle.FieldsValue["_point"] is point for handle in
            (fixed.FieldsValue["h1"], vertical["h1"], vertical["h2"], horizontal["h1"], horizontal["h2"])
        )
    arc.FieldsValue["f20"] = sum(row["d"].FieldsValue["h1"].FieldsValue["_arc"] is arc for row in values)


def make_sweep_profiles(system, settings, allocator, section_radius, path_radius):
    need_radii(section_radius, path_radius)
    plane = system.SystemValues.PlaneValues
    target = settings.TargetValue
    section = MakeCircleFeat(SECTION, system.RootValue, plane["x"], "x",
                             CircleInput((0.0, 0.0), section_radius, target.FileVersion), target, allocator)
    diameter = AddCircDimMut(section, (0.012, 0.012), True, settings.DesignIntent, settings.SelectedLeader, allocator)
    path, support, frame = BeginProfileMut(PATH, system.RootValue, plane["z"], "z", target, allocator)
    sketch = MakeSketchSeed(path)
    path.FieldsValue.update(MakeProfileData(sketch, support, frame))
    arc, points = make_path_arc(sketch, path_radius)
    radius = make_path_dimension(path, frame, sketch, arc, points, settings, allocator)
    publish_path_dim(sketch, arc, points, radius)
    return SweepProfiles(section.ProfileValue, path, diameter, radius)
