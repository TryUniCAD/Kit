from dataclasses import replace
from math import isclose

from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Scalars.ReadScalar import ReadScalar
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadMgrAtom import (
    ReadMgrAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.RootOrder import (
    ReadRootOrder,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    CheckChmfFile,
    ChmfRoleKey,
    ReadChmfRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfStock import (
    ReadChmfStock,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


def historical_roles(link, stock, selected, atom_id, header, *, is_face):
    wrapper_class, selection_class, mode = (
        ("moCompFace_c", "moFaceRef_c", 768)
        if is_face
        else ("moCompEdge_c", "moEdgeRef_c", 512)
    )
    wrapper = RequireNative(selected, wrapper_class)
    fields = wrapper.FieldsValue
    component = RequireNative(fields["f58"], "moUnitComponent_c")
    reference = RequireNative(fields["fe8"], selection_class)
    assert fields["f18"] == fields["f1c"] == atom_id
    assert fields["has_alias"] == component.FieldsValue["has_ext"] == 0
    assert component.FieldsValue["owner"] is link.ConfigValue.RootValue
    assert reference.FieldsValue["fe8"] == mode
    records = tuple(row["f08"] for row in NativeRows(reference.FieldsValue["f10"]))
    assert reference.FieldsValue["f08"] == len(records)
    if is_face:
        assert len(records) == 6 and records[-1] is None
        records = records[:-1]
    else:
        assert len(records) == 4
    owners = tuple(RequireNative(value) for value in records)
    histories = tuple(
        ReadChmfRef(link, value, stock, header, False) for value in owners
    )
    file = RequireNative(histories[0].FieldsValue["f08"], "moExtObject_c")
    assert all(history.FieldsValue["f08"] is file for history in histories)
    assert len(set(histories)) == len(owners)
    CheckTreeAlias(link, (wrapper, component, reference, file))
    CheckChmfFile(link, file, header)
    return tuple(map(ChmfRoleKey, owners)), file


def shell_prediction(bounds, thickness):
    xmin, ymin, xmax, ymax, depth = bounds
    width, height = xmax - xmin, ymax - ymin
    inner_width, inner_height, inner_depth = (
        width - 2 * thickness,
        height - 2 * thickness,
        depth - thickness,
    )
    assert min(inner_width, inner_height, inner_depth) > 0
    outer_volume = width * height * depth
    inner_volume = inner_width * inner_height * inner_depth
    volume = outer_volume - inner_volume
    return {
        "volume_mm3": volume,
        "area_mm2": 2 * width * height
        + 2 * (width + height) * depth
        + 2 * (inner_width + inner_height) * inner_depth,
        "centroid_mm": [
            (xmin + xmax) / 2,
            (ymin + ymax) / 2,
            (outer_volume * depth / 2 - inner_volume * (depth + thickness) / 2)
            / volume,
        ],
    }


def verify_generated_shell_owners(archive, link, case):
    _, width, height, depth, thickness, (x, y) = case
    resolved = link.ResolvedValue
    stock = RequireNative(resolved.RootsValue[-2], "moExtrusion_c")
    shell = RequireNative(resolved.RootsValue[-1], "moShell_c")
    prefix = replace(
        link, ResolvedValue=replace(resolved, RootsValue=resolved.RootsValue[:-1])
    )
    features = IndexFeatures(prefix)
    ReadRootOrder(prefix, features)
    owner, _, loop = ReadChmfStock(link, stock, features)
    xs = sorted({point.PositionValue[0] for point in loop.PointsValue.values()})
    ys = sorted({point.PositionValue[1] for point in loop.PointsValue.values()})
    depth_owner = owner.RequireDepth()
    actual_depth = depth_owner.DepthValue.value_mm
    assert len(xs) == len(ys) == 2 and actual_depth is not None
    bounds = (xs[0], ys[0], xs[1], ys[1], actual_depth)
    expected_bounds = (
        x - width / 2,
        y - height / 2,
        x + width / 2,
        y + height / 2,
        depth,
    )
    assert all(
        isclose(actual, expected, rel_tol=0, abs_tol=1e-12)
        for actual, expected in zip(bounds, expected_bounds, strict=True)
    )

    atom = ReadMgrAtom(link)
    atom_fields, shell_fields = atom.FieldsValue, shell.FieldsValue
    atom_id = atom_fields["f140"]
    stock_id, shell_id = NativeNodeId(stock), NativeNodeId(shell)
    assert ReadOutputAtom(stock) is shell_fields["f538"] is atom
    assert (atom_fields["f12c"], atom_fields["f130"]) == (stock_id, shell_id)
    assert atom_fields["f180"] == atom_fields["f1b0"] == 0
    assert stock.FieldsValue["has_f3d0"] == shell_fields["has_f3d0"] == 0
    assert link.ConfigValue.RootValue.FieldsValue["fe38"] is None
    assert archive.get("Contents/Config-0-Partition") is None
    CheckTreeAlias(link, (stock, shell, atom))

    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    removed = RequireNative(shell_fields["f828"], "suObList").FieldsValue
    assert removed["n"] == 1 and shell_fields["f820"] == 0
    (row,) = NativeRows(removed["items"])
    cap, cap_file = historical_roles(
        link, stock, row["o"], atom_id, header, is_face=True
    )
    edge, edge_file = historical_roles(
        link, stock, shell_fields["f848"], atom_id, header, is_face=False
    )
    sides = {
        ("moFromSktEntSurfIdRep_c", line.PermanentId, None) for line in loop.LinesValue
    }
    assert cap_file is edge_file and len(sides) == 4
    assert cap[0] == ("moEndFaceSurfIdRep_c", 1, 0) and set(cap[1:]) == sides
    assert len(set(edge) & sides) == 3 and set(edge) - sides == {
        ("moEndFaceSurfIdRep_c", 0, 0)
    }

    display = RequireNative(shell_fields["f818"], "moDisplayDistanceDim_c")
    (driver_row,) = NativeRows(display.FieldsValue["f850"])
    handle = RequireNative(driver_row["o"], "moFeatureDimHandle_c")
    dimension = RequireNative(handle.FieldsValue["ff0"], "ThreeDRadiusDim_c")
    parameter = RequireNative(dimension.FieldsValue["f28"], "moLengthParameter_c")
    CheckTreeAlias(link, (display, handle, dimension, parameter))
    native_wall = parameter.FieldsValue["f58"]
    cell = display.FieldsValue["f5b0"]
    assert cell["n"] == 1 and cell["elem"] == len(cell["data"]) == 8
    assert ReadScalar(cell["data"], 0, "f64")[0] == native_wall
    observed_wall = native_wall / 0.001
    assert ReadNativeName(parameter) == depth_owner.DepthValue.name == "D1"
    assert dimension.FieldsValue["f50"] != depth_owner.Dimension.FieldsValue["f50"]
    assert isclose(observed_wall, thickness, rel_tol=0, abs_tol=1e-12)
    return {
        "stock_feature": stock_id,
        "shell_feature": shell_id,
        "shared_atom": atom_id,
        "stock_bounds_mm": bounds,
        "wall_mm": observed_wall,
        "native_wall_m": native_wall,
        "selected_cap_roles": cap,
        "auxiliary_edge_roles": edge,
        "stock_dimension": depth_owner.Dimension.FieldsValue["f50"],
        "shell_dimension": dimension.FieldsValue["f50"],
        "selected_partition_cache": False,
        "predicted_geometry": shell_prediction(bounds, observed_wall),
    }
