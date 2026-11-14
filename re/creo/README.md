# Creo research

## State

The PSB container is mapped well enough to list sections, inflate payloads, extract the native thumbnail, and retain exact source bytes.
The native geometry, feature, parameter, and dimension record map is **not complete**.
There is no independent PSB writer and no acceptance result for a newly authored Creo part.

## Layout

| Path | Contents |
| --- | --- |
| `container/` | Header, table of contents, section storage, sample inventory |
| `data-model/` | Tagged stream, geometry, design, units, parameters, confidence |
| `oracle/` | Local Creo control procedure and observed results |
| `open-items/` | The writer gap and next measurements |

## Hard result

The local Creo 2027.2 installation opened a vendor empty-part control.
A hand-built legacy ASCII part was rejected.
No generated native part with a body has been accepted.

Do not describe container inventory or exact replay as a Creo writer.
The [CAD success criteria](../../Documentation/Reference/Operations/CadSuccessCriteria.md) remain unmet for parametric Creo output.

## Sources

- [Cadmpeg Creo specification](https://github.com/cadmpeg/cadmpeg/blob/main/docs/formats/creo_prt.md), CC-BY-4.0
- [TeamCraft Creo research](https://github.com/rudalabs/TeamCraft/blob/main/docs/src/research/creo-brep-preview.md)
- [Adapter change entry](../../Documentation/Changes/Creo/CreoPsbContainer.md)
