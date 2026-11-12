# Independent ASM binary import framing

The independently authored cylinder SMB was valid without changing a byte. Its SHA-256 is `e543149d548412263728f3c33cabf115badbbc459d43e5a124a8df8f62d2e407`. Fusion 2706.1.17 accepted it through `TemporaryBRepManager.createFromFile`, produced the expected solid, and retained the measured geometry after a native F3D save and reopen.

This establishes native acceptance of the bounded analytic-cylinder SMB writer. The F3D archive in this acceptance sequence was authored by Fusion. This result does not establish an independently authored Fusion document, feature graph, body identity map, or parametric history.

## Why the first import route failed

`ImportManager.createSMTImportOptions` validates the extension as `.smt`. Supplying `.smb` fails option creation. Renaming binary bytes to `.smt` passes that extension check and sends the data through a text-oriented route. That failure was not evidence that the binary record stream was malformed.

The installed Python API documents `TemporaryBRepManager.createFromFile` as accepting SMT, SMB, SAT, and SAB at `Contents/Api/Python/packages/adsk/fusion.py:81145–81152`.

The native implementation also distinguishes those routes by extension before parsing:

| Evidence owner | Static arm64 address | Behavior |
| --- | --- | --- |
| `XLayer10.dylib` | `0xb0060–0xb00e8` | `SMTImportOptions::onValidateExtension` compares a four-character extension with `.smt` |
| `FusionXLayer10.dylib` | `0x168b00` | `TemporaryBRepManager::createFromFile_raw` entry |
| `FusionXLayer10.dylib` | `0x168c94–0x168ce4` | `.smb` dispatches to `Ns::ASMInterface::loadSmbFile` |
| `FusionXLayer10.dylib` | `0x168d50–0x168d78` | `.sat` and `.smt` dispatch to `Ns::ASMInterface::loadSatFile` |
| `NsASMInterface10.dylib` | `0x4ac4c–0x4ad04` | SMB loader constructs `SMIRestore`, executes restore, and retrieves entities and units |
| `NsASMInterface10.dylib` | `0x499b8–0x49a0c`, `0x49bc0–0x49bd8` | File mode selects the text/binary Boolean passed to `SMI_RESTORE` |
| `libASMkern232.dylib` | `0x1a90bc–0x1a90f0` | Restore Boolean true constructs `SmtFile`; false constructs `SmbFile` |

No extra standalone wrapper, compression, or embedded-record envelope was required. The same `ASM BinaryFile8` framing used by embedded Fusion SMB streams is accepted through the supported SMB route. The accepted standalone sample has no history partition or Fusion-specific body-map identity attributes.

## Header fields and unit semantics

The accepted binary begins with a 15-byte ASCII signature, followed by four signed integers in the width selected by that signature. `ASM BinaryFile8` uses eight-byte little-endian words here. The accepted values are `(23200, 0, 2, 2)`.

| Field | Accepted value | Recovered meaning |
| --- | --- | --- |
| `save_format` | `23200` | Version prefix used by the native save/restore version calculation |
| `stored_record_count` | `0` | Omitted record count in a streaming save; it does not mean an empty model |
| `top_level_entity_count` | `2` | Number of initial root entities, including the ASM header entity and the one body |
| `flags` | `2` | File-format revision is in bits 1–7; bit 0 has history-save control behavior and cannot alone determine whether a history partition exists |

The previous research name `first_owned_record` for the third word is misleading. The writer builds a root list by adding `ASMHeaderManager::get_ptr` at `0x1a8200–0x1a8218`, appending the input root entities at `0x1a821c–0x1a8238`, counting that list at `0x1a8488–0x1a8498`, and passing its count as the third header argument at `0x1a8524–0x1a8534`.

The initial header call supplies zero as its second argument at `0x1a852c`. An optional later rewrite supplies the emitted record counter at `0x1a8648–0x1a8680`. The reader admits zero in modern versions at `0x1aa570–0x1aa584` and initially reserves a default capacity instead at `0x1aa5cc–0x1aa5d8`.

For `save_format > 20999`, `version_from_header_data` at `0x1a7d64–0x1a7d7c` calculates:

```text
restore_version = save_format * 100 + ((flags >> 1) & 127)
```

The accepted header therefore selects `2320001`. `232.5.0.65535` in the ASM header record is the kernel build identity, a different value from this file-format revision.

The initial save path takes bit 0 from its history Boolean, then combines the file-format revision shifted left by one at `0x1a84a8–0x1a84fc`. Ordinary entity-list save passes false at `0x1a7ff4`; save-with-history passes true at `0x62c80c`. However, the header-rewrite path at `0x1a8638–0x1a8640` reconstructs flags from the revision alone. A clear bit 0 is therefore not proof that history data is absent. Actual history boundary records must be inspected.

`BinaryFile::write_header` at `0x53dc10` emits the signature and four untagged words. `BinaryFile::read_header` at `0x53deac` recognizes the ASM signature. The terminal characters `4`, `5`, `8`, and `9` encode integer width and byte order; the observed `8` profile is the admitted little-endian, eight-byte case. This research does not add support for the other profiles.

After the four words, `FileInfo` writes three strings and three real values:

1. Product identity
2. Kernel/build provenance string
3. Timestamp string
4. Units metadata
5. Kernel absolute resolution
6. Kernel normal resolution

The string writes occur at `0x1a6c78–0x1a6d18`; numeric writes occur at `0x1a6dbc–0x1a6dd0`. `FileInfo::restore` reads that same order at `0x1a6f9c–0x1a6fd4`. The resolution values are kernel metadata; their names do not establish millimeter units independently of the model coordinate convention.

The SMB import wrapper scales every restored body by `restored_units / 10` before exposing it in Fusion centimeters. This is explicit at `FusionXLayer10.dylib:0x168dd0–0x168e1c`. The independent binary writes units metadata `10` and converts input millimeter coordinates to centimeters. Consequently the wrapper scale is one. This is consistent with the accepted physical dimensions. The standalone text writer instead writes metadata `1` and millimeter coordinates; these are two coherent unit representations, not different shapes.

Eight-byte storage does not make all integer semantics unrestricted 64-bit values. `BinaryFile::safe_read_long` at `0x53c710–0x53c77c` verifies that the eight-byte result equals its sign-extended 32-bit value. Header reads make the same check. The distinct `int64` token remains a separate type.

## Native acceptance evidence

The parent agent performed the native calls serially. This investigation executed only file reads, disassembly, and evidence generation. The authoritative report is [BinaryTemporaryAcceptance.json](../../LocalOracle/Brep/BinaryTemporaryAcceptance.json).

| Measurement | Persistent body | Reopened native F3D |
| --- | --- | --- |
| Solid bodies | 1 | 1 |
| Faces / edges / vertices | 3 / 2 / 2 | 3 / 2 / 2 |
| Volume, cm³ | `7.7754418176350715` | `7.7754418176350715` |
| Center, cm | `(2.0000000001568523, -3.0000000000000004, 1.0500000000000003)` | Same |
| Minimum bounds, cm | `(0.5, -4.5, 0.5)` | Same |
| Maximum bounds, cm | `(3.5, -1.5, 1.6)` | Same |

The expected analytical center is `(2, -3, 1.05)` cm. The measured difference is numerical noise. The saved native F3D SHA-256 is `ce4ae6efcdb7814eb06284eb1b0eb3858bf80451fa3b13d31971676d11ce360c`.

The temporary body's `physicalProperties.centerOfMass` initially returned `(0, 0, 0)` despite correct volume and bounds. After the same body was added to a new direct-design document, the center was correct and remained correct after save/reopen. This is an observed context-dependent API result for this controlled case, not evidence that all temporary bodies always report an invalid center. Persistent-body measurements are required for this acceptance sequence.

## Reproducible static evidence

[InspectStatic.py](InspectStatic.py) reads the installed binaries with `otool`, captures bounded instruction ranges and image hashes, inventories the independent candidate, and snapshots the parent's acceptance report. It does not load native libraries or execute product code.

[StaticEvidence.json](StaticEvidence.json) contains the exact instructions, image digests, candidate digest, and acceptance report read during this investigation. All addresses are arm64 Mach-O slice addresses before the runtime slide, for deployment `b43a07003c01dd54425db484d23b1c5e6248a21d`.

The acceptance route is to retain the `.smb` extension, use `TemporaryBRepManager.createFromFile`, add the returned body to a fresh controlled direct design, inspect persistent geometry, and save/reopen through Fusion. No corrective binary mutation is supported or needed by the evidence. Independent generation of an embedded SMB payload is established for this analytic cylinder; independent assembly of the surrounding native Fusion document and parametric history remains separate work.
