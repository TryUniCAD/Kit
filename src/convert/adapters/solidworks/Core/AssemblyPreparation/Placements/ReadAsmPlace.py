from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.MakePlaneFrame import (
    MakePlaneFrame,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.TypedMates.ReadMateFrame import ReadMateFrame
from interchange.assembly.ComponentInstance import ComponentInst


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
        (Matrix[3] * 0.001, Matrix[7] * 0.001, Matrix[11] * 0.001),
        (Matrix[0], Matrix[4], Matrix[8]),
        (Matrix[1], Matrix[5], Matrix[9]),
    )
    return OccurrenceIn(Value.name, FrameValue)
