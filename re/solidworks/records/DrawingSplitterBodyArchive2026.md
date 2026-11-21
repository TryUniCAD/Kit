# Embedded drawing splitter linkage in SOLIDWORKS 2026

Both actual originals now advance through the environment and embedded splitter to the next `moBomInfoMgr_c` schema-one boundary. Full Definition parity remains incomplete. The preceding actual source probes both failed at the missing embedded method layout `uiSplitterInfo_c.Serialize`. Neither environment nor secondary splitter completion was credited. This tranche explicitly links that existing shared layout into the drawing profile; it adds no native class header, schema admission, field rule, constructor, saved value, or writer capability.

Task: PR121 drawing embedded-splitter dependency. Owner: `flag_ownership`; delivery PR: #121. Dependency: [the environment reader and bounded native owner](DrawingUserEnvironmentArchive2026.md). Exit: exact embedded dispatch and current field grammar, minimal source linkage, independent prior-profile replay, and the actual original outcome or next fail-closed boundary. Complete semantic and held-out writer verdicts remain separate.

## Concrete embedded owner

All relevant body addresses refer to `slduiu.dll` SHA-256 `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`, version `34.5.2.0604`. The [JSON proof](DrawingSplitterBodyArchive2026.json) retains the exact actual table, runtime identity, original-image hashes, complete functions, and call context. It references the unchanged full environment proof instead of inferring a body from source bytes.

The `uiUserModelEnv_c` constructor `[0x497d5740,0x497d57aa)` calls concrete splitter constructor `0x497d5600` for members `+0x10` and `+0xe0`. The splitter constructor `[0x497d5600,0x497d5731)`, 305 bytes, SHA-256 `283f93ac5bdf4367ed13ce996872fd8e1444772a5d1cbad678671c95959ecabf`, installs actual primary `0x4a65e720`. RTTI identifies `uiSplitterInfo_c` with direct `su_CObject` and `CObject` parents.

The selected drawing environment omits the first splitter through its already bound document-kind test. Its second splitter call uses the actual receiver `environment+0xe0`, passes the same incoming archive, and dispatches virtual `+0x28`: store at `0x497d5ffa`, read at `0x497d6118`. That slot selects `0x497d5b00`. No class/object tag appears around the embedded method call.

The complete splitter serializer `[0x497d5b00,0x497d5ed7)` is 983 bytes, SHA-256 `dee8484e884bbb8fd19a4dc22095ec5c9df7e35835c0d0b7cfd92057261eebd9`. This is the same independently bound body already documented with the environment. Its `.Serialize` SDK identifier denotes an embedded field grammar, not a newly read runtime class name or schema word.

## Current grammar and linkage

For the ordinary version-19000 profile:

1. Eight `u16` headers: `f08,f0c,f10,f14,f18,f1c,f20,f24`
2. Exactly `f08` rows, each containing exactly `f0c` columns
3. Each cell: embedded transform `xa`, embedded transform `xb`, `a:u16`, `b:u16`, `c:f64`, `d:CString`

Native read gates for cell `b`, `c`, and `d` are respectively `>=0x45d`, `>=0x1b6`, and `>=0xbdb`, all active at 19000. Current store always writes those fields. The existing native `mgXform_c::save/restore` imports own the two transforms. Their shared rule is already present through drawing `KBlankLayouts → KResolvedLayouts → KConfigLayouts` geometry fields.

Native zero-extension of header words and `b==0xffff` to runtime zero repair are separate from raw storage. The existing shared codec retains the source words. It does not allocate native UI grids, run settings-dependent legacy cache repair, or infer supported arbitrary grid dimensions.

The SDK change is exactly one mapping entry in [the drawing environment fields](../../../src/convert/adapters/solidworks/Drawing/Definition/Linked/Fields/EnvironmentFields.py): reuse `KDocEnvironmentFields["uiSplitterInfo_c.Serialize"]`. The [shared field definition](../../../src/convert/adapters/solidworks/Archive/Definition/Fields/DocEnvironmentFields.py), runtime schemas, aliases, map counters, scalar behavior, count limits, and drawing version/context gates are unchanged.

The preceding failure came from sparse layout composition: importing the containing environment tuple did not import its separately keyed embedded method. `GetLayoutMut` truthfully recorded the missing layout and raised `BodyUnsupported`. See [the explicit embedded-rule gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/Qualification/EmbeddedBodyLayoutsNeedExplicitLinkage.md). There is no guessed empty body, opaque fallback, or fabricated runtime schema to suppress that diagnostic.

## Evidence boundary

The exact single SDK path passes AST, Black, Ruff, scoped strict Mypy, scoped strict Pyright, steering, and the recorded-payload static scan. The first source candidate remains retained for its initial Black line wrap; the corrected source has an identical AST. The worker ran no SDK probe, codec, local test suite, vendor application, or VM operation. The corrected closure contains 4,351 source files. Root independently passed all 43 prior-profile workers on the corrected exact source. Both actual original probes preserve source immutability and advance beyond the preceding embedded-layout failure to `moBomInfoMgr_c` schema one. The inspector does not expose a separate environment completion counter; the next-class result and source call order establish this limited progress, not complete stream parity. The [custody receipt](../measurements/2026/DrawingSplitterBodyReader01.json) binds both results and retains the earlier real failure.

No constructor or writer rule changes. Original complete-source semantics, frozen drawing writer admission, native usability, and held-out writer acceptance remain unqualified unless their independent evidence establishes them. The original writer rejection is not changed by reader progress.

The mandatory stopping conditions remain “The first is success under every criterion on this page.” and “The second is the end of the available context.” Missing grammar remains work.
