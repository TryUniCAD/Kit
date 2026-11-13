from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint

KFrontMatrix = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    -1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


def FrameAxes(PlaneRole: str) -> tuple[dict[str, object], dict[str, object]]:
    if PlaneRole == "xz_plane":
        return MakePoint(0.0, 0.0, 1.0), MakePoint(1.0)
    if PlaneRole != "xy_plane":
        raise ValueError("Fusion part sketches lie on the XY or XZ plane")
    return MakePoint(1.0), MakePoint(0.0, 1.0)


def FrameMatrix(PlaneRole: str) -> dict[str, object]:
    if PlaneRole == "xz_plane":
        return {"entries": list(KFrontMatrix)}
    return {}
