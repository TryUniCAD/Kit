# Typed single-solid body labels and B-rep ownership

The public part reader now has a bounded projection for the actual body label in the disclosed SOLIDWORKS 2026 SP05.2 single-solid saves. It binds the active native partition, the real archive atom, its producing feature and the complete decoded B-rep before changing a neutral body's label. It does not use the Solid Bodies folder caption as that label, invent a body identity, alter the native payload, enable a writer, or qualify a new native body-name constructor.

Task: `B04-SW2026-NAMED-BODY-READ`. Owner: the PR #121 configuration/header lane, with independent product verification and integration by root. Delivery: PR #121. Dependencies: the complete version-19000 Config/Resolved codec, modern partition grammar, typed topology and the disclosed named-driver source cohort. Exit condition for this reader slice: real labels and a complete design-body/B-rep bijection on all four disclosed saves, unchanged unrelated semantics and payloads, and preservation of the old read path for the controlled unsupported output-owner variants. That condition passed the independent root replay. Named-body writing and original held-out qualification remain separate work.

## Sources and native ownership

The original getter, atom-name holder and active-partition ownership are recorded in [NamedBodyOwnership2026.md](NamedBodyOwnership2026.md) and its machine record. The four inputs are `NamedCorner` and `NamedCenter`, each before and after explicit renaming. They are disclosed discovery controls. Their six-process native naming lifecycle remains in [SdkPartNamingArchive01.json](../measurements/2026/SdkPartNamingArchive01.json); this reader proof adds no vendor process or newly saved native result.

The first profile requires an ordinary container version 4 and document version 19000, selected `Config-0`, one configuration, one neutral design body and one decoded B-rep body. The actual `Config-0-Partition` must carry its witnessed modern active and rollback payloads. The attached public payload must equal that selected active payload, and an independent decode of it must equal the public B-rep.

The new partition reader owns typed fields for the 23 reached current/base record classes. It verifies the schema descriptor, current WORLD and history marks, reference domains, complete active record inventory, attribute definitions, and reciprocal ownership chains. The admitted topology has one live solid body, a void and solid region, two shells, six faces, six loops, 24 fins, 12 edges, eight vertices, six plane surfaces, 12 lines and eight points. The outer void shell's null direct body pointer is qualified through its actual region; it is not changed to a guessed body pointer.

The body-to-atom join uses the actual BODY-owned attributes and their field positions:

| Native owner | Meaning used by the reader |
| --- | --- |
| `ATOM_ID_2001`, field 1 | Exact atom `f140`, within the actual owning manager's sole member |
| `BODY_MATCH`, field 0 | Exact atom `f180` and `f1b0`; independent from the BODY transmit index |
| `LAST_BODY_MODIFYING_FEATURE_ID`, field 1 | Exact atom `f130`, `f12c`, actual boss `f08`, and the existing neutral body's final feature |
| Actual boss `f528` | The sole member must be the same atom object as the manager's member; `f530` and `f538` alternate paths are not admitted |

The atom must be the only real `moAtom_c` in the resolved map, not an equal copied object. The final public feature and all complete B-rep face, loop, fin, edge, vertex, surface and curve identities must agree with the selected typed topology. The generic decoder's encoded pointer domain is transmit index plus one; its connectivity-derived B-rep body identifier is not a BODY transmit index. The reader preserves that existing identifier and supplies an explicit `BrepBody.design_body_id` link to the existing `DesignBody.id` after verifying the full bijection and coordinates.

`moAtom.f19c` is not used as a face count. The pinned constructor seeds it to six, and the real display getter identifies its display-mode role. Six faces in these saves do not make that field a topology count.

## Label admission and preservation

For the baseline source, `f18` is null, `f18c` is one, no explicit `SDL/TYSA_NAME` attribute exists, and the unique `SWIMPLICITBODYNAME_ID_U` value supplies the label. For the renamed source, the real `moNodeName_c.f08`, `f18c=0`, explicit body-owned `SDL/TYSA_NAME` character value and implicit Unicode value must agree. Printable ASCII is the measured encoding boundary; conflicting labels, an explicit Unicode alternative, nonprintable characters, the internal-name alternative and ambiguous owners retain the existing path.

The projection retains the original design-body identifier, final feature, geometry, parameters, feature history, payload bytes and all unrelated metadata. Its provenance identifies the actual atom source span and selected partition. The new `solidworks.native_body_names` and `solidworks.native_body` metadata describe this ownership proof only. Their `complete` status does not claim complete format conversion or a qualified writer.

Unsupported containers, releases, configurations, partition schemas, body inventories or output paths do not receive a speculative label. The existing strict geometry error, tessellation policy and history-only behavior remain in force. In particular, `include_brep=False` retains the prior body projection. No-cache parts with a populated atom manager are outside the current strict prism-reconstruction profile, so this change does not qualify a new no-cache named-body input.

## Independent process evidence

The [process receipt](../measurements/2026/SdkNamedBodyRead01.json) records the read modes, source hashes, comparisons and negative results.

Root's `RootReplay03/Replay.json` has SHA-256 `ac0aeaebb22b8f0d2e3b32c288f230ba73f5db3122889200d5df83b3aa85033e`. The candidate closure contains 4,329 files and is SHA-256 `cc8c4550aa01afebd5bca64de7b6f94ff429e92e97fa51aa1cc91abc240fe1a7`; it was unchanged after the replay. The 48-path owned-source manifest is `e5db79bc2a5cceb67c08b791b1b2f4f9b84acb5ba2ab05eced191a3da3452213`. The exact successful observer-tool manifest is `cd66021dcccaf90937d980d9c9e9ac9323dbff62058206a9219d211b0dbb02fb`.

All 22 fresh baseline/candidate processes and 55 paired mode comparisons passed. Each worker read through the real `solidworks.sldprt` public adapter in default, repeated default, no-tessellation, history-only and lenient modes. The four positive states preserved every unrelated semantic fingerprint and native payload hash. The seven controlled malformed output variants were missing, empty, duplicated, wrong-class or foreign output atoms, an alternate input atom and a dedicated output path. Their public documents matched the prior reader exactly; the candidate did not project a name or bypass a geometry failure. Public reads attempted zero audited file accesses and imported no research implementation. Original inputs remained unchanged.

The malformed fixtures are made solely inside the research observer by decoding and re-emitting a disclosed control's resolved stream. Their container repacking uses that control's native container framing because its file ID is not one of the generic generated-container IDs. This is negative-reader fixture preparation, never a production writer path, generated compatibility claim, template in `src`, or delivered native candidate.

Earlier observer failures are retained: the first used the short unregistered format ID, subsequent probes encountered lazy standard-library or validation-module imports under the no-file-access audit, and the first negative repacker omitted the required native container signatures. Root repaired only observer setup and kept all SDK sources and prior reports unchanged. The successful replay uses registered format ID `solidworks.sldprt`, verified codec/validation imports before the audit, and explicit malformed-control framing. Those setup failures are not product failures.

The original 47 sources passed Ruff, strict Mypy, strict Pyright, steering and the donor scan. The independently bound output-owner extension passed Ruff, strict Mypy and strict Pyright. Black was applied to actual file contents, including the Core paths affected by [the force-exclude gotcha](../../../Documentation/Gotchas/Tooling/Formatting/BlackForceExcludeMatchesCore.md). All Windows and held-out inputs remained outside this local proof.
