# Non-ASCII body-name ownership and frozen controls

The exact 2026 native getter distinguishes a character attribute from a Unicode attribute by its registered definition and accessor. This record describes the source rules and the frozen discovery controls. The subsequent [measured reader record](SdkUnicodeBodyNames2026.md) binds the native results and public reader tests. The original named hold-outs remain sealed.

Task: `B04-SW2026-UNICODE-BODY-READ`. Owner: the PR #121 configuration/header lane; root owns native authoring, product verification and integration. Delivery: research for PR #121. Dependencies: the exact-build body-name getter, typed modern partition grammar, actual archive atom owner and the already disclosed `NamedCorner`/`NamedCenter` baseline sources. Exit condition before an SDK change: fresh controlled non-ASCII saves with an exact native label, complete Config/Resolved/partition readback, and agreement or a measured precedence relationship among the archive name, explicit character/Unicode attributes and implicit Unicode attribute.

## Exact native distinction

`sldgcu.dll` is SHA-256 `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594`, preferred base `0x43740000`. The original `gcBody_w::getName` range is `[0x43890a30,0x43890b46)`, SHA-256 `d413c4252d70cf1261d8f412f8c1e39e7049e1b043ab3b04c1a412cea21931bb`.

1. At `0x43890a54`, find `SDL/TYSA_NAME`; at `0x43890a65`, select that attribute from the actual supplied body. If present, `0x43890afb` reads character field zero with `gcAttrib_w::getString`, then a wide CString is made through MFC import ordinal 290.
2. Only when that actual character attribute is absent does the routine find `SDL/TYSA_UNAME` at `0x43890a7d` and select it from the same body at `0x43890a8b`.
3. At `0x43890ac4`, the Unicode path calls `gcAttrib_w::getUnicodeString` with field zero. If neither attribute is present, the getter returns empty.

This priority is an exact source rule for `gcBody_w::getName`. The separate higher-level COM body-name and archive-atom relationships still need the new controlled observations; the getter alone must not be described as a measured complete `IBody2.Name` dispatch trace.

The `setName` routine `[0x438a43b0,0x438a4482)` is SHA-256 `18da9acd71b2d65a5cb33ed928a837a1dd3026752fb8dabdcc9a31dadee647c3`. It finds or creates `SDL/TYSA_NAME`, calls the actual `KERNEL32!WideCharToMultiByte` import at `0x438a4440` with code page 3, flags zero, null-terminated input, a 256-byte output buffer and null default-character observation pointers, then calls `setString` field zero at `0x438a4450`. It has no observed branch that creates `SDL/TYSA_UNAME` instead. Requesting a non-ASCII BSTR therefore does not itself prove which attribute owner will be saved by the complete application path.

Code page 3 is the current thread's ANSI code page, while UTF-8 is 65001. That distinction is fixed in [Microsoft's WinNls declarations](https://raw.githubusercontent.com/microsoft/win32metadata/main/generation/WinSDK/RecompiledIdlHeaders/um/WinNls.h). The [official conversion documentation](https://learn.microsoft.com/en-us/windows/win32/api/stringapiset/nf-stringapiset-widechartomultibyte) says the thread code page can vary and documents replacement/best-fit behavior. The observed call does not prove a UTF-8 character payload, a portable machine code page, or a lossless non-ASCII round trip. The MFC character-to-wide conversion's exact runtime code-page path is not closed by the ordinal import alone.

The Unicode accessor takes a different route. `gcAttrib_w::getUnicodeString`, `[0x43a1acc0,0x43a1aced)`, forwards through `0x43e87170` to the explicitly imported `sldgciParau!gciAttrib_w::getUnicodeString`, entry `0x33038f90`. That original module is SHA-256 `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`. The inspected accessor range is `[0x33038f90,0x33039022)`. Its lower kernel dispatch table slot is not assigned a guessed API identity here.

The separate implicit-name getter at `0x32f81da0` selects the actual body-owned `swImplicitBodyName_ad` and calls that Unicode accessor with field zero at `0x32f81df6`. The corresponding implicit-name setter receives a wide CString through `sldgcu` `0x438a4560` and its GCI import. It is distinct from the narrow `setName` routine.

The pinned `sldworks.exe` manifest resource `[24,1,1033]` is valid XML, 1,927 bytes, SHA-256 `1f7a46bdad68d8a811ac461373b78f89be3a07a9f1a40872b050d3764cb49285`. It contains no `activeCodePage` entry. This does not identify the effective runtime code page; it prevents treating an unobserved manifest-level UTF-8 declaration as evidence.

## Typed archive and kernel owners

The existing modern schema represents `CHAR_VALUES` as kind 84 with character units, and `UNICODE_VALUES` as kind 98 with unsigned 16-bit `w` units. The explicit character definition observed on the four ASCII saves is `SDL/TYSA_NAME`, type ID 8017, field types `(3,)`. The implicit definition is `SWIMPLICITBODYNAME_ID_U`, field types `(10,10)`, first field reaching kind 98 and second null in those saves. No saved `SDL/TYSA_UNAME` instance has yet been observed in the authorized cohort; its numeric definition ID and complete saved representation remain unqualified rather than extrapolated from 8017.

The current bounded SDK character lexer also decodes its `c` fields as ASCII. A non-ASCII character payload may therefore require a separate raw-byte research observation before semantic projection can even run. That is an explicit parser admission limit, not evidence that the saved character bytes are invalid. The SDK remains unchanged until the actual new control representation is known.

The real `moAtom_c.f18 -> moNodeName_c.f08` already uses the archive's typed string codec. Its exact original string must round-trip through Config and Resolved before it can substantiate a Unicode projection. The ASCII reader's actual manager/feature-output/body-tag joins and complete B-rep binding remain prerequisites; a matching string in an unrelated record is insufficient.

The candidate read rule, pending observation, is:

- Collect the unique actual archive atom name and body-owned character, explicit Unicode and implicit Unicode attributes without normalizing or coercing their text.
- Decode declared kind-98 values as strict UTF-16 code units, preserving valid surrogate pairs and exact code-unit round trips. Reject isolated surrogates, embedded nulls or unqualified field shapes. Do not treat the tuple as independent Python Unicode scalar values.
- Retain raw character bytes and their declared owner. Do not guess UTF-8 or a host ACP merely because one decoding looks plausible.
- Apply the source-proven native character/Unicode selection rule only where the corresponding accessor semantics and measured higher-level body label agree. If archive, implicit and selected explicit owners disagree, preserve the existing unsupported path until their exact native precedence is proven.
- Cover implicit field-one content, alternate attributes, simultaneous character/Unicode owners and non-ASCII character conversions only when actual source evidence closes those states. The present ASCII witnesses do not close them.

The packet prepares disclosed native measurements for the admission boundary.

## Frozen source-authoring command

Private packet: `NamedBodyUnicodeSource01/Packet01/Trial.json`, SHA-256 `9e8d5bdebea994c735a7aa378146767ccfaf518ba0b3c7001913013ed7ff01a9`. It copies only the explicitly disclosed corner and center baseline saves, plus the established pristine L1 control. Three independent labels cover precomposed accents, Greek/CJK BMP characters and a non-BMP character requiring a UTF-16 surrogate pair. Filenames and driver names remain ASCII so this is a body-text differential.

Each case first measures the actual unchanged source, saves its baseline, changes only `IBody2.Name`, measures the immediate and rebuilt states, saves the renamed document, then checks it in a fresh process before and after rebuild. Three live driving dimensions, the complete feature tree, volume, area, mass and centre of mass must remain unchanged. All original files are hash-immutable. The eight planned processes include matching pristine before/after lifecycle controls. No name is set on a generated Kit part, and no writer result is produced.

Root stages the exact packet to an unused guest directory and invokes its own frozen tool with the registered oracle interpreter:

```powershell
& $OraclePython -B C:\KitUnicodeBodySource01\Tools\AuthorUnicodeBodyNames.py verify C:\KitUnicodeBodySource01\Trial.json --packet-sha256 9e8d5bdebea994c735a7aa378146767ccfaf518ba0b3c7001913013ed7ff01a9
& $OraclePython -B C:\KitUnicodeBodySource01\Tools\AuthorUnicodeBodyNames.py run C:\KitUnicodeBodySource01\Trial.json --packet-sha256 9e8d5bdebea994c735a7aa378146767ccfaf518ba0b3c7001913013ed7ff01a9
```

Only the root-owned `prlctl exec --current-user "Windows 11"` transport and COM oracle are authorized to run these commands. `$OraclePython` is the previously verified guest interpreter, not a filename or PATH guess. Terminal observations are `Inspection/Result.json`, with per-phase records and separate baseline, renamed and reopened saves. A setter rejection, substituted label, warning, changed geometry or unhealthy control is retained as an unsuccessful source boundary rather than removed from the comparison.

Initial metadata-only verification passed with `processes_started=0`. The later native measurement passed all eight fresh processes, including both healthy controls. The disclosed cases kept their exact authored labels during save and reopen. [Native result identity and SDK readback](SdkUnicodeBodyNames2026.md#source-and-measured-ownership)
