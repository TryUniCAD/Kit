from math import radians
from importlib import import_module
from pathlib import Path
import sys

from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import FrameXform
from convert.adapters.solidworks.Archive.Construction.Geometry.MakePlaneFrame import MakePlaneFrame
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginRef import MakeOriginRef
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.EmitRevStreams import EmitRevStreams
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevPart import MakeRevPart
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Construction"))
make_request = import_module("MakeRevolveRequest01").make_request


def make_cold(axis, reverse, rotated=False):
    name = f"PrincipalReader{axis.upper()}{'Reverse' if reverse else 'Forward'}"
    spec = {
        "name": name, "radial_mm": (6.25, 19.125), "axial_mm": (-8.75, 24.5),
        "axis_x_mm": 3.5, "axis_span_mm": (-14.625, 31.0), "angle_deg": 73.0,
        "edit_angle_deg": 123.0, "reverse": reverse, "created_at": 1795189000,
        "self_path": rf"C:\KitPrincipalReader\{name}.SLDPRT",
    }
    doc, settings = make_request(spec)
    part = MakeRevPart(doc, settings)
    system = part.SystemValue
    datum = system.SystemValues.PlaneValues[axis]
    principal = PrincipalFrame(axis)
    frame = principal if not rotated else MakePlaneFrame(
        principal.OriginValue, principal.AxisV, tuple(-word for word in principal.AxisU)
    )
    if rotated:
        geometry = ArchiveNode.RequireNode(datum.FieldsValue["f6f8"])
        geometry.FieldsValue["f20"] = FrameXform(frame)
    profile = part.ProfileValue.ProfileValue
    profile.FieldsValue.update(
        pd_f78=MakeOriginRef(datum, system.RootValue, axis), pd_ff0=FrameXform(frame)
    )
    start = tuple(
        centre + u * spec["axis_x_mm"] * 0.001 + v * spec["axis_span_mm"][0] * 0.001
        for centre, u, v in zip(frame.OriginValue, frame.AxisU, frame.AxisV, strict=True)
    )
    part.AxisReference.FieldsValue.update(
        fc8=dict(zip("xyz", start, strict=True)),
        fe0=dict(zip("xyz", frame.AxisV, strict=True)),
    )
    streams, _, _ = EmitRevStreams(
        system, (*system.FeatureValues, profile, part.FeatureValue),
        part.HeadersValue, part.DefinitionValue, settings, part.PlanValue,
    )
    if axis == "z" and not rotated:
        assert streams == part.StreamsValue
    spec["angle_rad"] = radians(spec["angle_deg"])
    spec["support_id"] = datum.FieldsValue["f08"]
    return BuildSldprt(streams, FormatVersion=4), spec
