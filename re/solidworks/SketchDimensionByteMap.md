# SOLIDWORKS sketch dimension byte map: P04 and P02

This is offline reader evidence, not a writer specification. Offsets are decimal,
zero-based, and half-open. Scalar values are little-endian binary64 metres.
**Decoded** means the typed reader and the observed records establish the meaning
in this layout; **constant** means the bytes agree across the specified captures
but their independent meaning or generation rule was not established.
**Unknown, varying** means the field cannot be emitted from these findings.

## P04: RectangleSketch, Contents/Config-0

The public neutral reader already binds each named driving parameter to the
two ordered endpoints of its saved perimeter edge. It does not infer the
operands from the dimension name or global axes. The reopened measurements
identify the same type-1 point pairs. In the YZ capture the pair bound to
width changes from `[(0,1),(3,4)]` to `[(0,1),(2,3)]`; the height pair changes
in the opposite direction.

The provenance marks the dimension **body**, not the preceding class token.
The width and height bodies have identical framing except for the node name,
which is one UTF-16 code unit longer for height.

| Width | Height | Classification and field |
| --- | --- | --- |
| −2–0 | −2–0 | Decoded: compact class reference to `sgPntPntDist` |
| 0–4 | 0–4 | Constant: zero leading word; role unknown |
| 4–6 | 4–6 | Decoded: class reference to `moLengthParameter_c` |
| 6–28 | 6–30 | Decoded: `moNodeName_c` class reference and counted UTF-16 name |
| 28–44 | 30–46 | Constant: four parameter words; roles unknown |
| 44–48 | 46–50 | Decoded: empty framed text; role unknown |
| 48–50 | 50–52 | Decoded: null object pointer |
| 50–58 | 52–60 | Decoded: parameter value in metres |
| 58–59 | 60–61 | Decoded: absent alternate length override |
| 59–61 | 61–63 | Decoded: null object pointer |
| 61–65 | 63–67 | Decoded: dimension ID, 27 for width and 28 for height |
| 65–77 | 67–79 | Constant: three zero words after ID; roles unknown |
| 77–79 | 79–81 | Decoded: null object pointer |
| 79–81 | 81–83 | Decoded: active state |
| 81–82 | 83–84 | Decoded: absent alternate name |
| 82–86 | 84–88 | Decoded: type 1, unsigned point-to-point distance |
| 86–88 | 88–90 | Decoded: two operands |
| 88–90 | 90–92 | Decoded: not deleted |
| 90–92 | 92–94 | Constant: zero reserved field |
| 92–94 | 94–96 | Decoded: absent transform |
| 94–106 | 96–108 | Decoded: first `sgPointHandle`; class reference, slot, local owner, flags |
| 106–118 | 108–120 | Decoded: second `sgPointHandle`, same layout |
| 118–126 | 120–128 | Constant: four 16-bit trailer words; roles unknown |
| 126–128 | 128–130 | Decoded: trailer null object pointer |
| 128–152 | 130–154 | Constant: three zero doubles at the end; role unknown |

Across all eleven captures only these exact body-byte indices change: width
`[50,57)`, `[108,109)`; height `[52,59)`, `[110,111)`. These differences
are within the scalar and second handle slot. There are no unknown-and-varying
bytes **inside the body** in this corpus. Constant bytes are not proven defaults.

### P04 display link

The display is a separate `moDisplayDistanceDim_c` object in the same stream,
not a pointer in the dimension trailer. `moSkDimHandleValG2_c` resolves an
archive object reference to the current `sgSketch`, then reads a 32-bit
dimension slot. In baseline-a the displays start at 15131 and 16574; their
handle bodies start at 15691 and 17134 and end at 15804 and 17247. The final six
bytes of each handle are the sketch reference (object 155) followed by slot 0
for width or slot 1 for height. The reader verifies the two trailing display
value copies against the linked dimension.

All eleven captures have 1443-byte display records for both dimensions.
The table groups fields that vary; the exact changed bytes are subsets of
these enclosing fields. All other display bytes are constant within each
named dimension across the eleven captures.

| Relative range | Classification and field |
| --- | --- |
| 426–450 | Decoded: text position (three doubles) |
| 695–711 | Unknown, varying: first two doubles in the array read by `ReadPlacement` |
| 799–815, 823–839 | Unknown, varying: pairs of doubles in that same array; the scalar edit changes only one double of each pair |
| 895–897, 903–905 | Unknown, varying: bytes in the next placement word group, read as `<i7H` |
| 969–977, 993–1001 | Decoded: the two corroborating dimension value copies read by `ReadCache` |
| 1349–1353 | Unknown, varying: one height-display word in the tail group read as `<2i3d2i`; changes on both `plane-yz` and `termination-through-all` without a height change |

Changing the driving value changes placement data as well as the
corroborating copies. A complete display serializer is not established.

## P02: CircleSketch, Contents/Config-0-ResolvedFeatures

The span at 6707 is 215 bytes and includes the class definition. The
measurements identify type 15 and a single circle operand. The neutral reader
already emits the named driving parameter and binds it to the native circle,
rather than to its centre point or to the construction origin.

| Range | Classification and field |
| --- | --- |
| 0–17 | Decoded: archive class definition for `sgCircleDim` |
| 17–21 | Constant: zero leading word; role unknown |
| 21–46 | Decoded: class definition for `moLengthParameter_c` |
| 46–74 | Decoded: `moNodeName_c` class reference and counted UTF-16 name |
| 74–90 | Constant: four parameter words; roles unknown |
| 90–94 | Decoded: empty framed text; role unknown |
| 94–96 | Decoded: null object pointer |
| 96–104 | Decoded: diameter in metres |
| 104–105 | Decoded: absent alternate length override |
| 105–107 | Decoded: null object pointer |
| 107–111 | Decoded: dimension ID 27 |
| 111–123 | Constant: three zero words after ID; roles unknown |
| 123–125 | Decoded: null object pointer |
| 125–127 | Decoded: active state |
| 127–128 | Decoded: absent alternate name |
| 128–132 | Decoded: type 15, diameter |
| 132–140 | Decoded: two serialized operand fields, not deleted, zero reserved and absent transform |
| 140–152 | Decoded: `sgArcHandle` class reference and local arc slot 0 |
| 152–183 | Decoded: `sgEntHandle` definition and invalid slot −2; not a second solver operand |
| 183–191 | Constant: two zero words in the trailer; roles unknown |
| 191–215 | Constant: three doubles (1, 0, 0); role unknown |

Only `[96,103)` changes within the body across the five committed P02 captures.
The radial display handle spans `[7641,7781)` in all five, binds sketch
object 173 and radial slot 0, and is followed by display-value data outside
the dimension body. The typed reader corroborates the copies at 8097 and 8121.
The independent diameter copy at 7863 is **unknown, varying** in purpose;
it tracks the size edit but is not one of the two returned caches.

## Verification and next captures

Compare the bytes of the streams after expanding the SLDPRT archive. Locate
each body through the public constraint's provenance and each display by
tracing `ReadDisplays` or `ReadRadialView` as the archive cursor advances.
Compare bytes within each named dimension, not by fixed stream address or by
the order of the neutral constraints. Cross-check type and operands against
`observations.reopened_files` in each capture's `measurements.json`. The
integration test withholds baseline-a, baseline-b, plane-yz and
termination-through-all from the P04 discovery set and tests all eleven;
it also exercises all five P02 files through the public reader.

Do not write either family from this map. For P04, save a rectangle-only
control twice, then change one thing per save: move only one dimension's
text, switch driving/reference state, reattach one operand without changing
the scalar, and change one driving value and rebuild. Repeat on another
plane; vary downstream features independently to isolate the height display
tail. For P02, add a move-only radial label capture and a two-circle sketch
with independently varied diameters to establish the owner of the extra copy.
Measure the display locations, operand IDs and driving state on fresh reopen.
A generated file still needs a clean SOLIDWORKS open and an edit/rebuild with
the intended geometry change, between healthy controls.
