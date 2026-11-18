# Body-name character payload uses the thread code page

Expectation: a non-ASCII COM body label or a `CHAR_VALUES` payload might imply UTF-8, or an automatic switch to `SDL/TYSA_UNAME`.

Actual source rule: in the pinned 2026 `sldgcu.dll`, `setName` creates the character `SDL/TYSA_NAME` owner and calls `WideCharToMultiByte` with `CP_THREAD_ACP` and a 256-byte buffer. The corresponding getter selects that character attribute first; it selects `SDL/TYSA_UNAME` only when the character owner is absent. The separate implicit body-name accessor is Unicode. Those storage owners cannot be collapsed into one assumed encoding.

Retain each owner and its raw typed payload. Decode declared Unicode units strictly and require exact archive and implicit Unicode agreement on a body with complete verified ownership. All three disclosed accent, BMP and supplementary-character cases preserved that agreement through native save and reopen. [Measured reader record](../../../../../../re/solidworks/records/SdkUnicodeBodyNames2026.md)

The original trace records exact module hashes, getter and setter locations, and code-page references. [Source rule](../../../../../../re/solidworks/records/NamedBodyUnicodeRead2026.md)
