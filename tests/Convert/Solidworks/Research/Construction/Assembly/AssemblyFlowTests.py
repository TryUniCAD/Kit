from tests.Convert.Solidworks.Research.Construction.Assembly.RunAsmCases import (
    RunAsmCases,
)


# complete coincident assemblies must retain real generated component and datum identities through independent whole stream process comparisons
def TestCoincident() -> None:
    RunAsmCases("coincident")


# complete parallel assemblies must preserve rotated placement configuration and external directory semantics across every admitted principal plane axis
def TestParallel() -> None:
    RunAsmCases("parallel")


# complete driving distance assemblies must allocate their real parameter dimension display and handle graph before publishing mate and wrapper identities
def TestDistance() -> None:
    RunAsmCases("distance")
