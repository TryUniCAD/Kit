# Creo state sections accept a minimal struct body, but `BasBasData` and `FeatDefsDtm` do not

## Expectation

Every Creo PSB section body carries real state, so a section body has to be authored
field-by-field before the vendor loader will accept the part.

## Actual behaviour

Most state sections load when their body is replaced by the smallest well-formed tagged stream for
their root struct:

```text
e0 00 <struct-name> 00 e3 f1
```

Measured on the retained control with `re/creo/tools/Subset.py` as the rebuild and `Author.py` as
the body source. Each row is one Creo 2027.2 launch:

| Minimal bodies added | Result |
| --- | --- |
| `BasicData`, `MdlStatus`, `FullMData`, `LargeText` | loads (`End`, `MT Part Solid`) |
| + 10 `ModelView#*`, `ColorSchemeInfo`, `ColorSchemeInfoNew`, `THMB_IMG_INDX`, `CGFMappingTable` | loads |
| + `BasicText`, `Geomlists` | loads |
| + `GeomDepen`, `DispCntrl`, `ActEntity`, `NeuPrtSld` | loads |
| + `DwgData`, `IdsGenInfoDb` | loads |
| + `ActDatums` | loads |
| + `FeatDefsDtm` | model-load crash, no `End` |
| + `BasBasData` (with the rest) | model-load crash, no `End` |

So 27 of the 31 plain sections are satisfied by an empty struct. Two are not, and both fail because
they carry model identity rather than optional state:

- `BasBasData` holds the model-defining scalars (`part_type`, `first_ent_id`, `model_eps`,
  `outline`, `attrib_array`, `max_part_size`). `Author.BasBasDataPayload` now emits it field by
  field, and a control container with 39 authored rows loads.
- `FeatDefsDtm` holds the datum placement records that the reader already decodes. It is still
  unauthored and remains the last plain blocker.

## Consequence

The authoring burden is much smaller than the section count suggests. A part can be built from:

- 11 grammar-authored bodies (`Author.AuthoredSections`);
- 27 minimal struct bodies (`Author.MinimalSections`);
- real `BasBasData` (`Author.BasBasDataPayload`) and `FeatDefsDtm`;
- the remaining compressed, binary, and free-space rows.

Measured: a control container with 39 of its 54 directory rows replaced by authored bodies loads in
Creo 2027.2 with `End` and `MT Part Solid`, and drops from `81539` to `31271` bytes.

## Workaround

Do not spend effort on empty state sections. Do not assume a minimal body is acceptable for
`BasBasData` or `FeatDefsDtm`: both fail silently at model load, without an error message, so a
missing `End` line in the trail is the only signal.

## Evidence

- `Documentation/Changes/Creo/CreoGenerativeAuthor.md` — section tables and launch logs.
- `src/convert/adapters/creo/Author.py` — `AuthoredSections`, `MinimalSections`,
  `EmptyPartSections`.
- `re/creo/tools/Subset.py` — rebuild used for every measurement.
