from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint


# explicit integer order must survive sorting without accepting boolean or ambiguous placement and mate positions
def ReadAsmOrder(Value: ComponentInst | MateConstraint) -> int:
    RequireAsm(
        type(Value.order) is int, "assembly order requires its exact integer domain"
    )
    return Value.order
