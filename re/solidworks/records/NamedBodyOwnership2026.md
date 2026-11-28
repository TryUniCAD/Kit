# Named solid-body ownership and reader boundary

The body-name storage and ownership rule is confirmed for four disclosed SOLIDWORKS 2026 SP05.2 saves. The authored label has an archive atom name owner as well as two kernel name attributes. A complete public body-name and B-rep binding is not implemented or qualified by this investigation. No named-body writer output, new native run, hidden source, or product verification is counted.

Task: `B04-SW2026-NAMED-BODY-READ`. Owner: the PR #121 configuration/header research lane; root owns product verification, integration and the Windows oracle. Delivery: research for PR #121. Dependencies: the ordinary version-19000 Config/Resolved graph, the current Parasolid partition grammar, the disclosed named-driver source receipt, and the existing geometry decoder. Exit condition for a later reader change: exact native labels and a complete body-to-B-rep ownership bijection on the independent controls, with unsupported and ambiguous inventories preserved or rejected explicitly.

## Evidence

The disclosed inputs are `NamedCorner` and `NamedCenter`, each in `Baseline` and `Renamed` author states. Their original custody, six native processes, healthy controls, fresh reopen and depth-edit observations remain in [the naming record](PartDriverAndBodyNames2026.md), [the archive receipt](../measurements/2026/SdkPartNamingArchive01.json) and [the strict-reader receipt](../measurements/2026/SdkPartNamingArchive02.json). Those inputs are discovery controls, not pre-writer held-outs for a new name constructor.

[The focused observation tool](../../tooling/sw2026/body/InspectNamedBodyOwners.py) reads only the four locked author files and their existing receipt. It checks all active typed record fields, registered definitions, reciprocal attribute chains, actual body and shell ownership, complete face/edge/vertex inventories, the archive atom/feature join, and the actual authored atom name holder. It re-emits all four complete partition streams identically. It does not call `open_document`, a public adapter read, a CAD runtime, or a writer. The final private observation is SHA-256 `04ea7d9a1026886d134fa5130c5db6c7f1000d8b08588c046d5d4e221cb924d9`; its unchanged 4,284-file SDK/research source closure is `5a57e4cf4857ad6ef49d465a192c7c336029d37423bd699e773d4082e2019eaf`. Root independently reran the exact parser closure and reproduced both hashes.

The accompanying [machine record](NamedBodyOwnership2026.json) contains the source identities and sanitized conclusions. Raw native listings and original instruction bytes remain outside the repository. The owned Hopper target was closed; REA reported `open=false` and `cleanup_pending=false`.

## Exact native getter

The original `sldgcu.dll` SHA-256 is `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594`, preferred base `0x43740000`. `gcBody_w::getName` occupies the inspected range `[0x43890a30,0x43890b46)`, original file offset `1375792`, SHA-256 `d413c4252d70cf1261d8f412f8c1e39e7049e1b043ab3b04c1a412cea21931bb`. REA assembly evidence is `ev_f3c83907744a20a6441ddd6152e4ebbafbdca53e97f2ca91ad103758885b1170`.

| Native site | Observed rule |
| --- | --- |
| `0x43890a4d` / `0x43890a54` | Resolve `SDL/TYSA_NAME` in the supplied entity's definition scope. The immutable ASCII literal is at `0x43f69488`, file offset `8551048`. |
| `0x43890a65` | Get the attribute from the actual supplied body, selector zero. |
| `0x43890afb` | Read character field zero when that explicit attribute exists. |
| `0x43890a76` / `0x43890a7d` | Only when the first attribute is absent, resolve `SDL/TYSA_UNAME`. Its literal is at `0x43f69498`, file offset `8551064`. |
| `0x43890ac4` | Read Unicode field zero on that fallback attribute. |

The supplied body's field ownership is decisive. The routine does not obtain a name from a feature-tree folder. The separate `gcBody_w::getSWBodyName` getter at `0x43893570` uses its internal body-name definition. The separate `getSWImplicitBodyName` entry at `0x43893620` forwards through `0x43e86230` into `sldgciParau.dll`. These are distinct APIs; their names do not establish interchangeability with `IBody2.Name`.

The native setter and measured saves bind the ASCII attribute to `IBody2.Name` for this cohort. The getter's character-to-wide conversion and setter's thread-code-page conversion do not establish UTF-8. Non-ASCII, embedded-NUL and maximal-length labels remain unqualified. The Unicode explicit fallback is source-proven but is not exercised by the two disclosed designs.

## Typed name owner

For the measured explicit label, the complete graph is:

`active BODY (12) -> owned ATTRIBUTE (81) -> registered ATTRIB_DEF (80) -> ATT_DEF_ID (79, SDL/TYSA_NAME)`

The definition has type ID `8017` and one field of type `3`. Its sole field reference reaches `CHAR_VALUES (84)`. The array count is the number of character bytes; the label has no inherited folder owner. Both renamed cases have one such attribute and both baselines have none. The kind-84 value is included in the selected geometry rollback's deletion inventory, already checked by the prior naming receipt.

The same rename also changes field zero of the existing body-owned `SWIMPLICITBODYNAME_ID_U` attribute. It changes from the creating feature label to the explicit label in both unrelated designs. This definition uses two fields of type `10` (`UNICODE_VALUES`, kind 98); field one is null in these four saves. `SW_INTERNAL_BODY_NAME` is absent in all four. A constructor must not infer that writing only one name owner is sufficient from the explicit character differential alone. This investigation writes neither owner.

The exact relationship between conflicting explicit, Unicode and implicit labels in the COM presentation remains unmeasured. A first public reader profile can cover the measured cases by accepting either a unique implicit label with no explicit attribute, or unique explicit and implicit labels that agree. It must not silently resolve a conflicting-name case from this cohort.

## Authored archive atom name

Both baselines have `moAtom_c.f18 = null` and `f18c = 1`. Both renamed saves have an actual `moNodeName_c` at `moAtom.f18`; its `f08` is the native explicit label, and `moAtom.f18c = 0`. That name agrees with both kernel attributes in each renamed file. The atom is the same actual object joined through `ATOM_ID_2001` and `BODY_MATCH`; it is not a synthesized folder or an unrelated named feature.

The original `sldmodu.dll` SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. [The atom pinning tool](../../tooling/sw2026/body/PinAtomNames.py) verifies the original constructor vtable and RTTI, follows selected slots and imports, and hashes the exact inspected native windows. It writes source facts only, never code listings.

| Native owner/site | Source-proven operation |
| --- | --- |
| Constructor `0x4bcede70`, vtable assignment `0x4bcede98` | Selects `0x4cff1620`; its complete-object RTTI identifies `moAtom_c`. The constructor writes the derived-name state at `0x4bcedf6d`. |
| `moAtom_c::setNameDerived`, `[0x4b293560,0x4b293567)` | Writes the supplied integer directly to `this+0x18c`. SHA-256 `799994ee76d7ef4505f9eafed113449c3d844fd82a06ea2eed006605c9fccb0c`. |
| Vtable `+0x88`, `moNode_c::name`, `[0x4c03e5c0,0x4c03e5d7)` | Returns the CString at the actual `this+0x18` holder's `+0x08`, or the shared empty string when the holder is null. SHA-256 `39844f5a8121579e8955cce70a6341ebc989ed3a52e7d29669a8a000892c46bf`. |
| `moAtomManager_c::getAtomFromName`, call at `0x4bcf2f34` | Walks manager-owned atoms and compares the requested name to each actual atom's `+0x88` result. The inspected range `[0x4bcf2ed0,0x4bcf2f7e)` hashes to `1b6c19089dfff50b502100986f60cb1be1854d1324d46f5f01f68f4932414fea`. The comparison is imported as MFC ordinal 2903; its case behavior is not promoted here. |
| `moAtom_c::setBody`, calls `0x4bcfb496` and `0x4bcfb4d7` | Calls the naming helper at `0x4bcfb7a0` with the actual atom, body and current feature-derived name. |
| Helper `0x4bcfb7a0`, name read `0x4bcfba4e`, dispatch `0x4bcfba85` | Examines the actual base/output atom ownership. The one-output path can reach that atom's `+0x88` name, and dispatches the current atom's `+0x3a8` name calculator when the selected atom has a nonempty name. |
| Vtable `+0x3a8 = 0x4bcf10e0`, branch `0x4bcf1286–0x4bcf12c5` | Reads the selected atom's actual `+0x88` name and copies it into the calculated result. |
| Helper call `0x4bcfb829`, IAT `0x4cd39ec0` | Passes that resolved string to the explicitly imported `gcBody_w::setSWImplicitBodyName`. |

This is a source-grounded authored-name propagation path. It does not prove that a newly constructed name-only atom will attach correctly to a regenerated no-cache body. The body allocator, atom manager membership, feature output ownership and rebuild lifecycle remain necessary inputs. A writer is still prohibited from promoting these captured states as a row or from assuming that the two observed flag values close every lifetime branch.

The second Hopper query was refused before launching an owned model document because of the known unrelated model lease. Only this task's logical target was closed. The native trace continued with the original PE and `/Library/Developer/CommandLineTools/usr/bin/llvm-objdump`; final REA state was closed with no pending cleanup. No foreign document or process was closed.

## Solid ownership and identity domains

All four files have one active `WORLD`, one live `BODY`, two regions, two shells, six faces, twelve edges, twenty-four fins and eight vertices. `WORLD.body` selects the body, `BODY.owner` returns to that world, and the body chain exhausts all active kind-12 records. The body points to the void region followed by the solid region. Both regions point to the same body. The solid shell has a direct body pointer; the exterior void shell's direct body pointer is null, and its region supplies the actual owner. Both face chains have exactly the same six faces.

The observation joins the body-owned `BODY_MATCH`, `ATOM_ID_2001` and `LAST_BODY_MODIFYING_FEATURE_ID` attributes to the one actual `moAtom_c` and actual extrusion:

| Native owner | Archive join |
| --- | --- |
| `BODY_MATCH`, integer field zero | `moAtom.f180` and `moAtom.f1b0` |
| `ATOM_ID_2001`, integer field one | `moAtom.f140` |
| `LAST_BODY_MODIFYING_FEATURE_ID`, integer field one | `moAtom.f12c`, `moAtom.f130` and actual extrusion `f08` |

The body transmit index, persistent node IDs, runtime body match tag, atom identity and feature identity are different domains. A saved body match tag changes across the two saves even though the body topology and design identity remain the same. No numeric value in this cohort becomes a fixed writer or neutral-body identity.

Each input also contains a separate `Config-0-GhostPartition`. The live ordinary partition contains an active geometry payload and a delta payload. A decoder must select the active partition for the actual selected configuration; it must not choose the first readable payload, a ghost partition, an unrelated configuration, or a rollback record as the named solid.

## First bounded SDK rule and proof plan

1. Admit only the proved version-19000 ordinary part, selected Config-0, current `SCH_3701250_37102_13006` partition grammar and one actual solid body. Preserve explicit failure for unknown configuration, schema, extra live bodies, detached attribute owners, duplicate definitions or names, invalid text, missing atom identity, or incomplete topology.
2. Resolve the registered definition and reciprocal body-owned attribute chains. Join the actual atom name holder and derived-name state as well. In the first measured profile, the authored atom name and explicit/implicit kernel labels must agree. A baseline has no authored atom name and uses its derived kernel label. Read actual source labels; never seed a label from the saved examples, folder text, an assumed body ordinal, or the creating feature name alone.
3. Establish the body-to-atom-to-feature join above. Keep the neutral design body's ID separate from its actual kernel transmit index and runtime tag. Expose native identities only as provenance or typed attributes, with explicit domain names.
4. Bind the selected payload to the B-rep actually attached to the public document. The existing `BuildTreeModel` may fall back to a derived body from face connectivity, while `ReadNativePart` constructs a single folder-named design body. Therefore a label-only replacement does not prove complete binding.
5. Require one complete decoded B-rep body and exact equality of all decoded face, edge and vertex identities with the typed body's reachable inventory. The generic XMT decoder retains transmitted pointer values; the research grammar exposes their zero-based indices. For this layout the former is the latter plus one, as established by `Cursor.pointer`, `XmtData` and the native topology record parsers. Do not join a derived body ID directly to a native body transmit index.
6. Set the validated B-rep body's `design_body_id` to the actual neutral design body ID, and require a nonempty bijection covering every neutral body and every B-rep body. `BrepModel.validate()` alone permits an empty design-body link and cannot prove this condition. Preserve all regions, shell uses, topology, analytic geometry, original payload bytes and provenance.
7. Root runs exact current-before/fixed-after public reads in fresh processes against the four locked discovery states, with unchanged topology, analytic geometry, complete semantic output except intentional body name/binding fields, payload hashes, and strict/no-B-rep/tessellation-option behavior. Add malformed-owner, duplicate/conflicting-name, wrong-config, ghost-only and multi-body negative controls at the archive boundary. Keep unknown native ownership explicit rather than dropping rows.
8. The smallest separate native diagnostic is an immutable research copy of a disclosed named control with only its live partition stream omitted, retaining the authored atom and all other streams. Compare initial body/name state, dimension edit, save and fresh reopen at matched paths between healthy controls. Retain the exact stream-deletion manifest. This is a vendor-derived diagnostic input, never a generated writer output or held-out acceptance case. A clean name survival would measure the archive-to-regenerated-name route; a failure would leave the allocation/load boundary open.
9. Before writer work, root locks new unrelated named-body cases and freezes the name construction rule and evaluator. Independently test names of different ASCII lengths, at least one non-English name for any wider encoding claim, body rename followed by feature/dimension edits, save and fresh reopen, and a multi-body distinction before enabling multi-body projection. Both healthy native controls remain mandatory.

The production reader implementation, root's process verification, named-body constructor, native generated-name lifecycle, and held-out qualification remain open. Existing no-cache geometry behavior is not changed: absence of a partition is not evidence of an explicit persisted body label.
