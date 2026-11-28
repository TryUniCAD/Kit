# Initial option state for the ordinary single-edge fillet

The SOLIDWORKS 2026 SP05.2 ordinary Fillet constructor allocates a
present, empty `su_CDWordArray` for `Fillet_c.fc20`. The Parasolid
solve accepts the empty array as its first-solve input. It fills six
words from the solved option state on the observed default save
branch. The initial writer rule is a typed empty array.
[Source receipt](../measurements/2026/EdgeFilletFreshOptions01.json)

## Constructor and argument ownership

The exported `Fillet_c` constructor in `sldmopartu.dll` at
`0x180269d00` calls the actual array constructor on `this+0xc20`
at `0x180269e77`. The implementation in `swccu.dll` clears the
data pointer and signed element count. Its write at `0x31a3bcc7`
establishes zero in the count at `+0x10`.

The operation at `0x1802a6cc0` takes the address of that same
member at `0x1802a87ca` and supplies it as the penultimate
explicit operand of `ramFilletEdge` at `0x1802a88dd`.
`sldgcu.dll` forwards it through its `0x43ca0b70` export and
`0x43e7f9a0` bridge to `sldgciParau.dll`. The actual
`gci_ramFilletEdge` loads the pointer at `0x33062174`. Its
small-profile dispatch at `0x3306233d` passes it through
`0x3306cbb0`, then `0x33070920`. That continuation owns the
ordinary option check.

## First solve and output allocation

| Native site | Observed operation |
| --- | --- |
| `0x33071b93` through `0x33071ba7` | A present array with count zero sets the fresh-options flag to one and skips reading items. |
| `0x33071bf2` through `0x33071c42` | The populated branch reads the already saved options into its live kernel state. |
| `0x33071d42`, `0x3307207a` through `0x330720a4` | The continuation reloads the fresh flag. Its result gate checks the status value `0x47d7`, then calls the option saver when the flag is set. |
| `0x33078109` through `0x33078126` | The saver appends six words through `su_CDWordArray::SetAtGrow` at the current count. |
| `0x33078128` through `0x330781b3` | When the default branch selector is zero, the saver replaces six initial sentinel values from the actual solved option state. |
| `0x33062fbb` through `0x33062fcf`, `0x3306373b` | The separate direct branch in the public kernel entry has the corresponding present-empty option path and calls the same saver. |

The six words in the disclosed source archives are saved solver state.
The cold rule follows the constructor and first-use path. Result surface
and edge allocation, the editable radius graph and a clean native
lifecycle remain independent qualifications.
[Saved source owner audit](EdgeFilletConstructionBoundary2026.md)
· [Accepted stock orientation](EdgeFilletStockAcquisition2026.md)

## Reproduce

The exact PE receipt covers four module digests, nine unwind ranges
and 37 selected instruction sites. The private Hopper decompilation
of the operation is REA evidence
`ev_034e22c67ce0d6d81371d8f8f655083468d7756052a569b4b09c4e1732f69c10`.
The recorded Apple LLVM instruction walk independently verifies the
addresses and call operands. The receipt retains only hashes,
addresses and imports.

```sh
python3.14 -I -B re/tooling/sw2026/edge_fillet_source/AuditFilletFreshOpts.py \
  --modules /disclosed/oracle/module-directory \
  --array /disclosed/oracle/swccu.dll --report /fresh/EdgeFilletFreshOptions.json
```

The report SHA-256 is
`65360804428c55b466be022b1d457c768df83fa76d0bb97e4e8d0a2ee6f8b047`.
This evidence ran zero native lifecycles and published zero fillet files.
