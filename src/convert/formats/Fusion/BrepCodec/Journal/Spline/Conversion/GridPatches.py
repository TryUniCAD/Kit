from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology


def GridPatches(
    Topology: CageTopology,
    Spokes: tuple[int, ...],
    Places: tuple[tuple[int, int], ...],
) -> tuple[PatchCell, ...]:
    Cells: list[PatchCell] = []
    for FaceIndex, Face in enumerate(Topology.Faces):
        if Face.IsHidden:
            raise ValueError("Fusion grid conversion does not convert hidden faces")
        LinkValue = Topology.Links[Face.OriginLink]
        Following = Topology.Links[LinkValue.NextLink]
        if Spokes[Face.OriginLink] != 3 or Spokes[LinkValue.NextLink] != 0:
            raise ValueError("Fusion grid conversion needs aligned face origins")
        Column, Row = Places[LinkValue.VertexIndex]
        if Places[Following.VertexIndex] != (Column + 1, Row):
            raise ValueError("Fusion grid conversion needs aligned face origins")
        Cells.append(PatchCell(FaceIndex, (0, 1, 0, 1), (-Row, -Column, 0)))
    return tuple(Cells)
