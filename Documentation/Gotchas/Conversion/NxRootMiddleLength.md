# The NX root section middle is variable length

## Expectation

The root object model section (section 3) carries a fixed 176 byte middle between the class registry and
the section trailer. `RootSection.RootMiddle` emits that middle from a counter and a seven byte anchor
identity, and `RootSection.MiddleStart` recovers it as `pointer - 176`.

## Actual behaviour

The 176 byte middle is the empty part form. A part with features carries a longer middle: the same
prefix and suffix, with a `03 03 02 00` table and object records inserted before the anchor.

```text
part        section 3 size  registry end  pointer  middle length
empty.prt              607         0x1a4      595            175
dim40.prt              607         0x1a4      595            175
block.prt             1319         0x1a4     1307            887
```

The middle starts one byte before the registry end, because the class region separator byte is also the
middle's first byte. For an empty part the first three bytes are `02 02 02`; for `block.prt` they are
`02 22 23`, and the `04 05 02 00` lane of the empty form is replaced by a run of `03 03 02 00` entries
followed by object records.

`MiddleStart` therefore returns the correct start only for an empty part. On `block.prt` it returns
`0x46b`, which is inside the record run, not the middle start.

## Workaround

`RootSection.AuthorSections` is only used for the empty part form, where the 176 byte middle and the
`pointer - 176` recovery are correct. Do not use it to author a part that already carries features: it
would discard the record run. A from-scratch writer for a featured part must emit the table and records
as well.

## Evidence

`re/nx/notes/DataModel.md` records the section 3 layout. The three part measurements above come from
`ReadPayload` on the corpus parts. See
[the root section build change](../../../Changes/Nx/NxRootSectionBuild.md).
