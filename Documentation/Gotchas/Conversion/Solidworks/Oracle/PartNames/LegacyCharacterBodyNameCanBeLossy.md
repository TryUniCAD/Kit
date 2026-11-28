# Legacy character body name can be lossy

Expectation: the body-owned `SDL/TYSA_NAME` character value supplies the complete `IBody2.Name`, or a Unicode name automatically uses `SDL/TYSA_UNAME`.

Measured behavior on the exact 2026 oracle: all three new non-ASCII controls retained their full COM labels and their actual authored archive/implicit UTF-16 names. `TYSA_UNAME` remained absent. The Greek/CJK character owner contained `?_?????`; a label with one supplementary character contained `?_??_?`, substituting twice for its surrogate pair. Accent bytes were invalid UTF-8 but reproduced the label under CP1252. That diagnostic does not establish a universal code page.

The lower-level character-first `gcBody_w::getName` getter therefore cannot be treated as the complete COM naming rule. Choosing that field, guessing UTF-8, or requiring its text to equal every wide label loses valid authored names.

Workaround: bind the real archive atom, actual body-owned implicit UTF-16 and complete B-rep ownership. For the qualified authored Unicode profile, require exact wide-owner agreement and retain the compatibility character bytes without interpreting them as the label. Keep ASCII coherence strict and reject unknown or conflicting wide states.

The native source identity, nine complete Config/Resolved round trips, eight controlled native processes and 56-worker SDK proof are in [SdkUnicodeBodyNames2026.md](../../../../../../re/solidworks/records/SdkUnicodeBodyNames2026.md). Named H inputs remain sealed and are not counted.
