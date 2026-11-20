from math import isfinite

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadThruStock import (
    ReadThruStock,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector

from BuildTwoStockShape import build_intent_shape
from ShapeIntent import ShapeIntent, Stock, require, scaled


def stock_rectangle(profile, link):
    loop = ReadThruStock(profile, link)
    lines = loop.LinesValue
    require(len(lines) == 4, "a cold stock requires four typed rectangle lines")
    point_ids = {end for line in lines for end in (line.StartValue, line.EndValue)}
    points = {point: loop.PointsValue[point].PositionValue for point in point_ids}
    xs = sorted({point[0] for point in points.values()})
    ys = sorted({point[1] for point in points.values()})
    require(
        len(points) == 4
        and len(xs) == len(ys) == 2
        and all(isfinite(value) for value in (*xs, *ys)),
        "typed rectangle vertices do not form four finite corners",
    )
    corners = ((xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1]))
    segments = {
        frozenset((points[line.StartValue], points[line.EndValue]))
        for line in lines
    }
    require(
        segments == {
            frozenset((start, end))
            for start, end in zip(corners, (*corners[1:], corners[0]), strict=True)
        },
        "typed rectangle lines do not bind the four adjacent sides",
    )
    return tuple(PlaneVector(*point) for point in corners)


def feature_id(node):
    return f"sldprt:feature:{NativeNodeId(node)}"


def support_id(profile):
    reference = RequireNative(profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
    datum = NativeRecord(reference.FieldsValue["ff0"]).get("f00")
    require(type(datum) is int and datum > 0, "cold stock has no actual support ID")
    return f"sldprt:plane:{datum}"


def stock_intent(owner, frame, link):
    depth = owner.RequireDepth().DepthValue
    extent = depth.value_mm
    require(
        owner.ModeValue == ExtrudeEnd.KBlind
        and owner.SecondModeValue is None
        and depth.name == "D1"
        and extent is not None
        and isfinite(extent)
        and extent > 0,
        "cold stock requires a finite active blind D1",
    )
    step = feature_id(owner.NodeValue)
    return Stock(
        step,
        f"sldprt:parameter:{NativeNodeId(owner.NodeValue)}:{depth.name}",
        support_id(owner.ProfileValue),
        frame,
        stock_rectangle(owner.ProfileValue, link),
        (-extent, 0.0) if owner.IsReversed else (0.0, extent),
    )


def output_body(owner):
    native_id = NativeNodeId(owner.NodeValue)
    return DesignBody(
        f"sldprt:body:{native_id}", ReadNodeName(owner.NodeValue), feature_id(owner.NodeValue)
    )


def rebuild_cold_stock_shape(ownership):
    link = ownership.LinkValue
    first, second, cut = ownership.OwnerValues
    first_frame, second_frame, cutter_frame = ownership.ProfileFrames
    selected_index = ownership.SelectedIndex
    require(selected_index in (0, 1), "cold cut has no unique selected producer")
    stocks = (stock_intent(first, first_frame, link), stock_intent(second, second_frame, link))
    selected, untouched = stocks[selected_index], stocks[1 - selected_index]
    from_support = support_id(cut.ProfileValue)
    cut_direction = scaled(cutter_frame.z_axis, 1 if cut.IsReversed else -1)
    stock_direction = scaled(selected.frame.z_axis, -1 if selected.extent[0] < 0 else 1)
    require(
        cut.ModeValue == ExtrudeEnd.KThroughAll
        and cut.DepthValue is None
        and cut.SecondModeValue is None
        and from_support == selected.support_id
        and cutter_frame == selected.frame
        and cut_direction == stock_direction,
        "actual through cut does not cover its selected stock",
    )
    profile = RequireNative(cut.ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    circle, driver = ReadLocalCirc(profile, link, AllowFree=True)
    require(
        driver is None and circle.ModeValue is None and circle.DriverName is None,
        "the cold cut requires its sole free circular profile",
    )
    cut_id = feature_id(cut.NodeValue)
    bodies = (output_body((first, second)[1 - selected_index]), output_body(cut))
    return build_intent_shape(
        ShapeIntent(
            selected,
            untouched,
            cut_id,
            f"{cut_id}:stock-body",
            CircleGeometry(PlaneVector(*circle.CenterValue), circle.RadiusValue),
            cut_direction,
            bodies,
        )
    )
