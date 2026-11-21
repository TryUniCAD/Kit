# Parse memory operands structurally

## Expectation

A RIP-relative operand string ends immediately after its closing bracket.

## Observed behavior

The disassembly helper failed on the store at `sldmodu.dll` address `0x4c721f5e`.
The operand string also contains a destination separator and another operand.
Parsing that complete string as a hexadecimal displacement raises an error.
Negative displacements also need their signed representation.

## Workaround

The helper now reads Capstone's structured memory operands.
It uses the signed displacement, instruction address and instruction size to
resolve a RIP-relative reference.
An absent import annotation does not prove that the binary has no import.
The ordinary PE import parser did not expose every descriptor in the studied image.
