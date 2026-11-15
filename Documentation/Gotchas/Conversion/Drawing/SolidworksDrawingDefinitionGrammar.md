# Drawing definition starts with a feature tree and a model reference

## Expectation

`Contents/Definition` is an opaque vendor stream, so a drawing cannot be
generated without a source container.

## Actual behavior

The stream is a serialized object graph with a recoverable prefix:

```
header            36 bytes   size version count flags guid
moDrawing_c                 root class declaration
moHeader_c                  user name logs and stamp
feature tree                name stamp action id records
feature tail                last name stamp and count
model reference             moExtObjectList_c with one moExtObject_c
units table                 moUnitsTable_c and its unit records
sheet                       moDrSheet and its reference plane
view                        moView_c and its reference plane
line styles                 moLineStyle_c and uiLineFontMgr_c
```

The feature tree starts after the `moStamp_c` record. Each record is a
`fffeff` string, the `0a800100` marker, the `0c80000000000000` block, a
four-byte timestamp, the `Created` action string, and a four-byte id. The last
record omits the marker and carries a timestamp and a count instead.

The model reference is a `moExtObjectList_c` with one `moExtObject_c` and one
`moCStringHandle_c`. The path string is followed by a two-byte class reference
whose index varies per drawing, then the model name string.

## Workaround

`DefinitionGrammar` parses and serializes the feature tree and model reference
byte-exactly for all ten tracked drawings. `DefinitionObjects` parses and
serializes the units table, sheet, view, and line style object blocks
byte-exactly. The units table is 1,510 bytes and constant across drawings except
for one class reference index. The object values are still raw bytes, so a
from-scratch drawing still needs the value semantics.

## Evidence

`TestDefinition` requires the serialized feature tree and model reference to
match the source bytes for `angled`, `minimal`, and `standard`. The same
round-trip holds for `orient-front`, `orient-top`, `projected`, `multisheet`,
`large`, `coincident`, and `scale3`.

`renamed-ref.SLDDRW` replaced the model reference name with `poly5x` and
SOLIDWORKS opened it with the same view position.
