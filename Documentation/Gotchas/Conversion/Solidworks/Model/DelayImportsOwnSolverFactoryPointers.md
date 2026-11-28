# Delay imports own the solver factory pointer

Expectation: an imported native call can be resolved by enumerating the PE's ordinary import directory.

Actual behavior: model callsite `0x4c4e4917` reads cell `0x4db4c388`, which is absent from the ordinary import list. The exact pinned model image binds it through its delay-import descriptor `0x4d713ce0` to `sldsvu.dll` symbol `?SOLVnewdimsys@@YAPEAVsolver_wrapper_c@@HW4SolverType@@@Z`. Its raw IAT value is delay thunk `0x4cb9dcad`. Treating this as a free registration callback loses the concrete solver receiver.

Workaround: inspect the exact PE delay-import directory within its declared size, honor its RVA/VA attributes, use PE32+ thunk width, and resolve the selected IAT cell through its paired name table. Verify the installed dependency's full hash before following its factory and actual vtable. Do not invoke the function to identify it.

Original model SHA-256: `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Descriptor SHA-256: `92098ad18df93879d62770299ff3d169d47255c7046cdab48d7569905070887f`. Full independent evidence is in this handoff's [lifecycle evidence](../../../../../re/solidworks/records/CircleLifecycleRules2026.json); no native library was loaded or called by the worker.

The [Microsoft PE specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#delay-load-import-tables-image-only) defines the delay descriptor and its attributes. Ordinary-import coverage and delay-import coverage are separate inventories.
