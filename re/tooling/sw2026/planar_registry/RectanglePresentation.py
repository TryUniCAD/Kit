from math import isclose, isfinite


def require(value, message):
    if not value:
        raise ValueError(message)


def point(value):
    require(set(value) == {"x", "y", "z"} and all(
        type(value[axis]) in (int, float) and isfinite(value[axis]) for axis in "xyz"
    ), "rectangle display point is not an ordinary finite typed triple")
    return [value[axis] for axis in "xyz"]


def observe(raw, sketch_name="Sketch1"):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

    link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
    (profile,) = (
        node for node in link.ResolvedValue.RootsValue
        if isinstance(node, ArchiveNode) and node.ClassValue.NameValue == "moProfileFeature_c"
        and node.FieldsValue.get("pd_f80") is not None and ReadNodeName(node) == sketch_name
    )
    sketch = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    dimensions = ReadLineDims(sketch, link)
    drivers = dimensions.DriverValues
    require(tuple(driver.NameValue for driver in drivers) == ("D1", "D2"),
            "the rectangle does not own its distinct width and height drivers")
    rows = {}
    for axis, driver in zip(("width", "height"), drivers, strict=True):
        fields = driver.DisplayValue.FieldsValue
        handle = driver.HandleValue.FieldsValue
        require(handle["ff0"] is sketch and handle["ff8"] == driver.IndexValue,
                "the display was not reached through its own actual rectangle driver")
        rows[axis] = {
            "profile": sketch_name, "driver": driver.NameValue, "metres": driver.MetresValue,
            "driver_slot": driver.IndexValue,
            "display_class": driver.DisplayValue.ClassValue.NameValue,
            "text_m": point(fields["f6a0"]["f38"]),
            "along_fraction": fields["f8a8"], "away_m": fields["f8b0"],
            "along_axis": point(fields["fa38"]), "away_axis": point(fields["f880"]),
            "start_m": point(fields["f958"]), "end_m": point(fields["f988"]),
            "under_text": fields["f8a4"] & 0x50,
            "centerline_route": bool(fields["f1014"] & 0x800),
        }
    return rows


def differences(source, generated, *, absolute=1e-12):
    changes = []

    def visit(first, second, path):
        if isinstance(first, dict) and isinstance(second, dict) and first.keys() == second.keys():
            for name in first:
                visit(first[name], second[name], path + "/" + name)
            return
        if isinstance(first, list) and isinstance(second, list) and len(first) == len(second):
            for index, (left, right) in enumerate(zip(first, second, strict=True)):
                visit(left, right, path + "/" + str(index))
            return
        equal = (
            isclose(first, second, rel_tol=0, abs_tol=absolute)
            if type(first) is type(second) is float
            else type(first) is type(second) and first == second
        )
        if not equal:
            changes.append({"path": path, "source": first, "generated": second})

    visit(source, generated, "")
    return changes
