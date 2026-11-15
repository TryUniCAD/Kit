# CATProduct object graph

## A product object is a `7c 05` record with a `7c 06` header and two name symbols

The product stream's object graph uses the same record framing as a `CATPart`:

```
7c 05 <u32 length> <one flag byte> 7c 06 <u32 length> <flags> ea <u32 object number> ...
```

The one flag byte after the `7c 05` length is why the child record is not at a fixed offset: it is
found by scanning for `7c 06` from `start + 6`. Getting that wrong silently returns zero objects.

The `7c 06` header is `<flag0> <flag1> <symbolA> <symbolB> ea <u32 number>`. `symbolA` and `symbolB`
both resolve against the OSMX symbol table and carry names, and `flag1` resolves too — it is
`0x04` for `ASMPRODUCT`, `0x00` for `CATCatalogManager`, and `0x09` for `A.1` or `_Component`:

```
Tilton_Set.CATProduct        15 objects   6 ASMPRODUCT, 5 CATCatalogManager, 4 A.1
Brake_Pedal_Assembly 2       24 objects   9 ASMPRODUCT, 7 _Component, 8 with no class symbol
Brake_Pedal_Assembly 1      153 objects  51 ASMPRODUCT, 53 _Component, 49 named Washer_5_DIN_433
```

## The names are real part and instance identifiers

`Brake_Pedal_Assembly - Backup 1.CATProduct` yields a readable bill of materials:

```
Banjo_goodridge_5091-02-03      Sensor_screw                 Washer_5_DIN_433
Washer_6_DIN_433                Nut_ISO_10511_M5             Nut_ISO_7040-M6
ISA_2080                        Brake_Pedal_Shaft            Reservoir_Holder
Brembo_remote_brake_fluid_reservoir_1
```

An instance object also carries `0xe6` doubles, which is where the placement transform lives.

## What is settled and what is not

Settled: the record framing, the one flag byte, the header layout, the class symbol, and that the two
name symbols are part and instance identifiers.

Not settled: which of `symbolA` and `symbolB` is the part and which is the instance. In
`obj 3 class ASMPRODUCT part Washer_5_DIN_433_1.2 instance Washer_5_DIN_433_1.3` the pair looks like
`(part, instance)` where the instance name is auto-generated from the part name, but in
`obj 4 class _Component part Sensor_screw.2 instance Washer_6_DIN_433_1.3` the "part" is clearly the
previous object's part, so at least one header shape has different flag positions. Treat both printed
names as "the two name symbols" rather than as a confirmed part/instance pair, and expect a
`_Component` object's header to be laid out differently from an `ASMPRODUCT` object's.

## Evidence

- `re/catia/tooling/ProductGraph.py`
- `Documentation/Gotchas/Conversion/Catia/CatiaProductOsmxHasTrailingData.md`
- `re/catia/examples/.CATProduct/` (three files, `153`, `24`, and `15` objects)
