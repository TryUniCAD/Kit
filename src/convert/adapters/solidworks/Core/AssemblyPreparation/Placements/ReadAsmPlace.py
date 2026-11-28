from math import inf as Infinity, nextafter as AdjacentFloat

from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.MakePlaneFrame import (
    MakePlaneFrame,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.TypedMates.ReadMateFrame import ReadMateFrame
from interchange.assembly.ComponentInstance import ComponentInst


# preserve an existing exact word or choose the nearest native translation that recovers the original
def EncodePlaceMm(Millimetres: float) -> float:
    NativeValue = Millimetres * 0.001
    if NativeValue * 1000.0 == Millimetres:
        return NativeValue
    NearValue = Millimetres / 1000.0
    for Candidate in (
        NearValue,
        AdjacentFloat(NearValue, -Infinity),
        AdjacentFloat(NearValue, Infinity),
    ):
        if Candidate * 1000.0 == Millimetres:
            return Candidate
    raise ValueError("native assembly placement cannot preserve the authored translation")


# portable column vector millimetre placement must become the proven native row vector metre frame explicitly
def ReadAsmPlace(Value: ComponentInst) -> OccurrenceIn:
    Matrix = Value.transform.values
    RequireAsm(
        len(Matrix) == 16 and Matrix[12:] == (0.0, 0.0, 0.0, 1.0),
        "portable placement requires its canonical affine last row",
    )
    NativeValue = tuple(
        Matrix[RowIndex + 4 * ColumnIndex]
        for RowIndex in range(4)
        for ColumnIndex in range(4)
    )
    _ = ReadMateFrame(NativeValue)
    FrameValue = MakePlaneFrame(
        (EncodePlaceMm(Matrix[3]), EncodePlaceMm(Matrix[7]), EncodePlaceMm(Matrix[11])),
        (Matrix[0], Matrix[4], Matrix[8]),
        (Matrix[1], Matrix[5], Matrix[9]),
    )
    return OccurrenceIn(Value.name, FrameValue)
