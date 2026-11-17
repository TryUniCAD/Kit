# Nested native saves can persist several header count copies

A completed ordinary configuration walk gives the expected expanded activity count. A later synchronized native save can persist different values in the two headers of a loaded subassembly and the active root.

In the first generated nested trial, the module's activity stayed one while both saved headers changed from one to zero. The root's activity stayed two, its ModelHeader kept two, and Header2 changed from two to three. The same saved files passed clean fresh reopen, rebuild and exact geometry checks.

During native readback, inspect each owning header and the configuration activity field independently. Bind the save context and exact file hashes to those observations. The generated construction profile retains its computed activity count, which passed the native trial. The full UI/header save-state reduction still requires its own evidence. [Typed before/after comparison](../../../../../../re/solidworks/records/GeneratedNestedAssemblySavedState2026.md)
