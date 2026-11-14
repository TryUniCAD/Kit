# Creo loader analysis

## Modules

The Creo 2027.2 install keeps the PSB loader in `Common Files\x86e_win64\obj`.
The three modules that matter for the part format are:

| Module | Bytes | SHA-256 | Role |
| --- | ---: | --- | --- |
| `coreutils_sh.dll` | 3,494,880 | `181e950b08087017e56dcb3c740e6844c8471932c7403238921bc58a77604756` | Container, table of contents, tagged-stream primitives |
| `metatoolsapi.dll` | 58,083,312 | `7c7219a49a1d161b161e01544d78320fc6b40e4d755de3ea2b25b777518db4aa` | Model classes and `CreoSerializer` |
| `diagexport.dll` | 37,903,328 | not yet hashed | Diagnostic export, secondary string hits |

The strings `UGC_TOC`, `Sld_Features`, and `FeatDefs` are present in all three.
`AllFeatur` and `VisibGeom` are not stored as plain ASCII in these modules; they are section names
resolved from the table of contents, not loader literals.

## Container primitives

`coreutils_sh.dll` exports the tagged-stream reader family:

| Export | Address | Role |
| --- | --- | --- |
| `exp_ugc_read_table_of_contents` | `0x18010d3e0` | TOC entry point |
| `exp_ugc_read_toc_from_file` | `0x18010d860` | TOC file reader |
| `exp_ugc_read_tagstruct` | `0x18010d440` | Tagged-structure wrapper |
| `exp_ugc_read_tagstruct_w_label` | `0x18010d460` | Tagged-structure reader with label |
| `exp_ugc_readstruct` | `0x18010dad0` | Structure dispatcher |
| `exp_ugc_read_structure` | `0x18010c400` | Field-by-field structure reader |
| `exp_ugc_read_binary_tag_low` | `0x18010ad40` | Low-level binary tag reader |

The TOC writer is `sub_1800e7510` (Hopper name) and uses the format string `"%s %d %d %d %d"` with a
row width of `0x51` (81 bytes). That matches the fixed-width `#UGC_TOC` rows the production reader
already parses.

`ugc_read_tagstruct_w_label` reads a tag name, looks up a field descriptor, and calls
`ugc_readstruct`. `ugc_readstruct` dispatches on the descriptor kind and calls
`ugc_read_structure`. `ugc_read_structure` reads the value according to the descriptor flags and
calls `ugc_assign` for the `ugc_xar_len` special case.

The field descriptor is a struct with these observed members:

| Offset | Meaning |
| ---: | --- |
| `+0x02` | type flags |
| `+0x06` | read callback |
| `+0x07` | read callback |
| `+0x08` | name pointer |
| `+0x0d` | read callback |
| `+0x12` | static storage |
| `+0x14` | size |
| `+0x15` | allocator |
| `+0x16` | read callback |
| `+0x20` | member offset |
| `+0x23` | last value |
| `+0x26` | last run mode |

The type flags are read as `flags & 0xf`; observed values include `0x0` (structure), `0x3` (string),
and `0xa` (string). The descriptor table is indexed by a 12-bit field id and a 20-bit namespace id
parsed from the tag name.

## Serializer API

`metatoolsapi.dll` exports the `CreoSerializer` class. The typed field methods are the authoritative
field grammar:

| Export | Address | Type |
| --- | --- | --- |
| `ProcStructField<int>` | `0x32d80` | integer |
| `ProcStructField<double>` | `0x32de0` | double |
| `ProcStructField<char*>` | `0x32e40` | string |
| `ProcStructField<xobject*>` | `0x32ea0` | object |
| `ProcStructField<CreoHandle<CreoSequence<...>>>` | `0x19f0d0` and following | array |
| `ProcEnum<...>` | `0x19ec30` and following | enum with dictionary |
| `ProcArray<...>` | `0x19df80` and following | array |
| `ProcMap<...>` | `0x1966c0`, `0x1968a0` | map |

The model classes are exported with their serializers:

| Class | Serializer |
| --- | --- |
| `CreoDesignatedItem` | `Serialize<CreoDesignatedItem>` at `0x1a2540` |
| `CreoItem` | `Serialize<CreoItem>` |
| `CreoParameter` | `Serialize<CreoParameter>` |
| `CreoParameterValue` | `Serialize<CreoParameterValue>` |
| `CreoDependency` | `Serialize<CreoDependency>` |
| `CreoInstance` | `Serialize<CreoInstance>` |
| `CreoSimpRep` | `Serialize<CreoSimpRep>` |

`CreoDesignatedItem` is the feature record. `CreoItem` is the model-level record. `CreoParameter`
and `CreoParameterValue` are the dimension and value records. The `ProcStructField` calls inside
each serializer give the field order and names directly.

### `CreoDesignatedItem` fields

`Serialize<CreoDesignatedItem>` at `0x1801d31e0` reads these fields in order:

| Order | Field | Type |
| ---: | --- | --- |
| 1 | `Id` | int |
| 2 | `Type` | enum |
| 3 | `SubType` | enum |
| 4 | `DsgnName` | string |
| 5 | `CreoName` | string |
| 6 | `OwnerId` | int |
| 7 | `OwnerType` | enum |
| 8 | `ModelLikeAttr` | enum |
| 9 | `FeatureStatus` | enum |
| 10 | `FeatureInStockAttr` | bool |
| 11 | `Symbols` | sequence of `CreoParameter` |
| 12 | `KeyPropsFlag` | bool |

`Id`, `Type`, `SubType`, `DsgnName`, `CreoName`, `OwnerId`, and `OwnerType` are the feature identity
and parent links. `Symbols` is the dimension sequence. This is the live feature-tree record.

### `CreoItem` fields

`Serialize<CreoItem>` at `0x1801d3a50` reads the model-level record:

```text
Name, Type, Title, Attribute, CreoLink, Tag, URL, CreoMetadata, CreoModel,
CreoIdSpaceMap, CreoConfigAssembly, PDMTrail, SimpRepArray, CreoModelDescriptor,
CreoModelParameters, CreoDependencies, CreoFamTab, RevNum, Verified,
CreoModelProperties, CreoDesignatedItems, CreoBoundingBoxMatrix, CreoUobjId,
Revnum, ReferenceControl, DbkeySize, CreoPDMTRecord, Application,
ApplicationInstanceId, Time, RevString, UserName, Action, StoredInMTM,
CreoPDMTrail, CreoPDMTRecordList, OwnerIdx, LastSaveIdx, CreoParamLabel,
Discr, Label, Icon
```

`CreoDesignatedItems` is the sequence of feature records. `CreoModelParameters` is the parameter
table. `CreoDependencies` is the dependency table.

### `CreoParameter` fields

`Serialize<CreoParameter>` at `0x1801d45a0` reads:

```text
CreoParameterValue, CreoParameterDef, CreoModel, CreoName, IsReadOnlyInProE,
IsReadOnlyInDB, IsSystemParameter, DBName, ValueType, Default, Restriction,
AccessTbl, DefinitOwner, IsChanged, QuantType, Description, Class, Label
```

### `CreoParameterValue` fields

`Serialize<CreoParameterValue>` at `0x1801d49e0` reads:

```text
Integer, Bool, Real, DoubleEpsilon, Unit, String, DateTime, Icon, Link, User,
CreoQuantType, Length, Time, Mass, Temperature, Current
```

`Real` is the numeric value. `Unit` is the unit token. `CreoQuantType` selects the quantity family
(`Length`, `Mass`, `Temperature`, `Current`, `Time`). This is the driving-dimension record.

## Evidence

- `coreutils_sh.dll` SHA-256 `181e950b...`; Hopper evidence for the TOC writer and the
  `ugc_read_*` exports.
- `metatoolsapi.dll` SHA-256 `7c7219a4...`; Ghidra analysis with 117,340 procedures and 185,141
  strings; export table read with `objdump -p`.
- The `Serialize<CreoDesignatedItem>` decompilation is the next artefact to record.

## Tagged-stream parser status

`re/creo/tools/TaggedStream.py` parses the explicit `e0 <type> <name> 00` fields, the
`e3`/`e2` structure begins, the `f1`-`f4` closes, the `e8`-`eb` compact integers, the
`f8`/`f9` arrays, the `e4`-`e7` repeats, and the one-byte double constants `0x0f` (0.0)
and `0x18` (1.0).

The parser stops on the `f7 <id>` field selection. The `f7` id is the model module's
global field id, not the stream's `e0` definition order. The stream defines a field
once with `e0`; later records select it with `f7 <id>`. The id is assigned by the
`ProcStructField` registration order in `metatoolsapi.dll`, so the parser needs that
registered table before it can resolve the later records.

The explicit first record and the empty control parse up to the first `f7`-only
record. The next step is to recover the registered field table from the
`ProcStructField` call order in the `CreoSerializer` serializers.

## Open questions

- The `Serialize<CreoDesignatedItem>` field order and names.
- The `CreoItem` base serializer, which carries the common feature fields.
- The `CreoParameter` and `CreoParameterValue` serializers, which carry the driving dimensions.
- The `VisibGeom` geometry serializer, which is not yet located by name.
- The `DispDataTable` compression variant.
