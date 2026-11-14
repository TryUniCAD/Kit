# Creo PSB container

## Scope

This page records the container evidence used by the `creo.prt` adapter.
It covers the `#UGC:2` part container, its table of contents, section framing, and Unix-compress payloads.
It does not claim complete record or geometry decoding.

## Sample inventory

No vendor sample is committed.
The following research samples were used locally.

| Sample | Bytes | SHA-256 | Origin | Use |
| --- | ---: | --- | --- | --- |
| `solid_start_part_mmks.prt` | 81539 | `b1374d7d356830300a8a4736b6f59a0ba50b5ef60938398a707fab02e69454aa` | Creo 2027.2 empty-part template | Control; section inventory; Creo open test |
| `lcd.prt.1` | 300015 | `288d994e493f1b1ec74aa8d272e1bc6b550857dfdb9df8a737fe402aecc2ed64` | Public Ender-3 repository | Real-world section coverage |
| `lcd_knob.prt.1` | 218938 | `13ac9c616e562e57f21afc6b33e2aaeba1ac83f44d51ec6eb082de9fd2817c30` | Public Ender-3 repository | Real-world section coverage |

The Ender-3 files keep their vendor extension revisions (`.prt.1`).
They are research inputs only.
Production code does not load them.

## Header

The first line is ASCII and begins `#UGC:2`.
The token after the signature is the model kind.
The observed kinds are `PART`, `ASSEMBLY`, and `PART/SHEETMETAL`.

```text
#UGC:2 PART 1934 1460 800 1 1 15 3700 2019344 000002cc \
#- VERS 0 0 \
#- HOST \
#- LINK \
#- DBID \
#- REVS 0, \
#- RELL 0, \
#- UOBJ_ID 1150729922 858940459 1131564914 \
#- MACH _Windows \
#- CMNM 017solid_start_part_mm.prt \
#-END_OF_UGC_HEADER
```

The last hexadecimal token of the first line is the section base.
For the control it is `0x2cc`, the byte immediately after `#-END_OF_UGC_HEADER\n`.
A base that does not follow the end marker is rejected.

The `#- CMNM` record stores a three-digit hexadecimal byte length, then that many bytes, then padding.
A repeated or malformed name does not establish a model name.

## Product banner and table

A product banner follows the header.
The control uses:

```text
#Creo  TM  Version P-60-34  (c) 2019 by PTC Inc.  All Rights Reserved. 6.0.3.0
```

The first `#UGC_TOC` line declares the entry count and fixed row width.

```text
#UGC_TOC 2 32 81 17#############################################################
```

Each row is 81 bytes in the control.

```text
<name> <offset-hex> <stored-length-hex> <expanded-length-hex> <version> <kind> <x> <checksum-a> <checksum-b>###
```

Offsets are relative to the header base.
Stored length includes the `#<name>\n` header.
Expanded length excludes the section header.
The `kind` field selects storage: `9` plain, `a` or `12` Unix-compress, `11` binary.
The control stores `THMB_IMG_MAIN` as kind `11`.

`NEXT_TOC_ENTRY` points to a continuation table.
The continuation uses the same header-relative base.

The checksum columns were not used for acceptance.
No reader path trusts a section until its header and extent validate.

## Unix-compress sections

A compressed payload begins `1f 9d <flags>`.
The low five flag bits give the maximum code width.
Bit 7 enables block mode.
Codes are packed least-significant-bit first.
The adapter bounds output to 64 MiB and rejects loops, undefined codes, and output beyond the declared expanded length.

## Section inventory

The control has 32 entries.
The Ender files add feature, geometry, display, and configuration sections.

| Section | Role | Confidence |
| --- | --- | --- |
| `VisibGeom` | Visible B-rep | Confirmed section; geometry body partial |
| `NovisGeom` | Construction geometry | Confirmed section; body partial |
| `AllFeatur` | Feature table | Confirmed section; records partial |
| `FeatDefs` | Feature definitions | Confirmed section; records partial |
| `FeatDefsDtm` | Datum feature definitions | Confirmed section; records partial |
| `SolidPrimdata` | Display strips for annotations | Confirmed section; body partial |
| `SolidPersistTable` | Persistence tables | Confirmed section; record partial |
| `BasicData` | Basic model data | Confirmed section; record partial |
| `UnitSystemDef` | Unit system | Confirmed section; record partial |
| `THMB_IMG_MAIN` | JPEG thumbnail | Confirmed JPEG marker |
| `ModelView#<id>` | Saved views | Confirmed section; view record not found |

## Current limits

- No section is decoded into neutral geometry in this change.
- Feature and B-rep records are not parsed into neutral records.
- The adapter retains the whole source so exact replay remains possible.
- The legacy ASCII `#P_OBJECT` form is recognised as a distinct generation but is not accepted by the current reader.

## Evidence

- [Data model](DataModel.md)
- [Oracle notes](../oracle/Oracle.md)
- [Writer gap](../open-items/WriterGap.md)
- [Adapter change entry](../../../Documentation/Changes/Creo/CreoPsbContainer.md)
