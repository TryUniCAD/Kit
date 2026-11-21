# Native entry cells may contain managed tokens

## Expectation

A native-looking indirect jump cell contains a callable address, or its target must be an ordinary PE import.

## Actual behavior

The pinned mixed-mode `doccplu.dll` string-name helper at `0x180050170` jumps through a cell whose original value is `0x0600014a`. It is not a native PC or ordinary import. The exact CLI `VTableFixups` entry covers that 64-bit cell. The matching MethodDef in the same artifact/MVID is the actual `ATL.+` helper used to concatenate the configuration storage name and downstream suffix.

Treating that word as an address, selecting a neighboring export label, or stopping at a failed normal-IAT lookup would lose the real name-construction edge. The token is meaningful only with this exact artifact SHA-256 and MVID; equal token numbers in other builds do not prove identity.

## Workaround

Check the PE's CLI header and exact fixup table before interpreting an unresolved cell. Bind the declared method, signature and original IL hash with stateless metadata inspection, retaining the difference between declaration, static data flow and runtime execution. Do not load or invoke the assembly merely to resolve it.

The [numeric/source record](../../../../../../re/solidworks/records/DownstreamStandaloneStore2026.md) supplies the fixup, method, signature and native evidence. Vendor code/listings remain outside the repository, and no native execution is claimed.
