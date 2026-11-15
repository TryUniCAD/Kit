# Disassemble from an instruction boundary

## Expectation

A hexadecimal address near a constructor is a safe place to start disassembly

## Observed behavior

Starting at `sldmodu.dll` address `0x4c452bc0` starts inside an instruction
The disassembler produces plausible instructions from those remaining bytes
Their operands do not describe the constructor
The confirmed constructor starts at `0x4c452ac0`

## Workaround

Start at the function entry or a boundary established by earlier decoded instructions
Do not infer fields from a range that starts at an arbitrary address
PE unwind fragments can split a logical function, so their end address can also truncate a constructor
Follow the actual control flow when a fragment ends before the function returns
