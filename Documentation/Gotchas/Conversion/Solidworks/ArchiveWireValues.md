# Archive wire values differ from loader state

## Expectation

Loading a record and storing its runtime values reproduces its bytes.

## Observed behavior

The 2026 light loader at `sldmodu.dll` address `0x4bc0b030` consumes a scalar
and clears the runtime field at `this + 0x36c`.
Other load paths coerce nonzero scalars to boolean values.
A codec that stores only the resulting runtime state can lose the original wire value.
The byte-identity instrument must expose those differences.

## Workaround

Preserve the wire scalar separately from its normalized state.
For synthesis, compute each field from its classified model role.
A preserved wire value is not a proven constant or a builder default.
See the [2026 schema guide](../../../../re/tooling/sw2026/serial/README.md).
