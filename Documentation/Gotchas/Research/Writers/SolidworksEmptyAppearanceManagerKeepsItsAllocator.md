# An empty appearance manager retains its allocation history

An empty `PWMaterialManager_c` reference list does not mean its two preceding words are fixed defaults. They preserve the unsigned64 next-appearance ID as signed low/high halves. The ordinary part guard currently admits the measured `(6, 0)` profile, so otherwise complete native saves with counters 4, 7 and 11 refuse with `alternate renderer profile`.

The existing PR #121 general Definition codec and `ReadEmptyAppr` preserve these owners without changing the ordinary guard. Public SDK geometry can also be returned with diagnostics while ordinary Definition admission refuses. Report those outcomes separately; neither return value proves lossless presentation. Do not replace the counter with 6 or drop the manager to obtain acceptance.

Use the [pinned inspection procedure and measured controls](../../../../re/solidworks/records/ResavedRendererRead.md) to identify the actual owner. Any broader ordinary acceptance belongs to a separately reviewed PR #121 extension with exact allocator preservation and the existing populated/foreign-owner refusals intact.
