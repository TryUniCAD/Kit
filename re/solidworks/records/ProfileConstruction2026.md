# SOLIDWORKS 2026 profile construction

Status: constructor helpers only, no generated profile or pad accepted

This extends [PolygonConstruction2026.md](PolygonConstruction2026.md)
The eight schema ladder controls have contributed to derivation and are not held-out inputs
The oracle owner must hash and lock new polygon controls before family writer code uses them

## Additional constructor rules

Binary hashes are bound by [Manifest2026.json](../v2026/Manifest2026.json)
Addresses use `sldmodu.dll` base `0x4b140000`, `sldmgu.dll` base `0x31dd0000`, and `sldmfcu.dll` base `0x3c800000`

| Field or operation | Rule | Evidence and confidence |
| --- | --- | --- |
| Normal profile entity `dflt` | `0`, because normal `moProfileFeature_c` virtual `+0x1ed8` returns zero | Constructor `sldmodu 0x4c0ca780` installs vtable `0x4d0e8e80`; slot target `0x4b27cbe0`; entity predicate `0x4c3e22e0`; confirmed static |
| Entity visibility | Layer `-1`, by-layer mask `31`, colour `0xffffffff`, line type `-1`, line width enum `-1`, visibility flags `3` | Entity constructor `sldmodu 0x4c3e1030` passes explicit arguments to `0x4c151050`; confirmed static |
| Entity line width | `f06=0`, `f00=-1.0` | `sldmodu 0x4c3e1085` passes enum zero to `sldmfcu 0x3c84a8f0`; confirmed static |
| Visibility line width | `f06=-1`, `f00=-1.0` | `sldmodu 0x4c3e10f2` passes enum minus one to the same constructor; confirmed static |
| Deferred indices | Keep endpoint and handle targets as object references, resolve owning-array indices when the field is read for storage | Native point/line lookup and framing addresses in the polygon ledger; derived implementation |
| Transform | Basis rows, authored translation, scale one, no perspective extension | `sldmgu 0x31e26880`, `0x31f09820`, `0x31e03ce0`; confirmed static |
| Sketch line display | A null sketch line-display pointer is serialized through the default line-display constructor: empty string, width enum `-1` and float `-1.0`, line type `-1`, final integer `1` | `sldmodu 0x4c5916f0` null-pointer branch; `sldmfcu 0x3c802910`; confirmed static |
| Sketch collections | Fresh entity, dimension, pattern, and auxiliary arrays are empty; counts derive from their current collections | `sldmodu 0x4c495450`; confirmed static |
| Relation manager | Relation list and equation-value map are empty | `sldmodu 0x4c603200`; confirmed static |
| Block manager | Block map, secondary map, and handle-data map are empty | `sldmodu 0x4c8f5ac0`, `0x4c8f9680`; confirmed static |
| Loop and slot managers | Loop collection is empty; slot counter `f10=0` and slot collection empty | `sldmodu 0x4c452ac0`, `0x4caace30`; confirmed static |
| Profile raw storage | The dynamic-array pointer at profile-data `+0x190` starts null; its serializer emits only u32 element size zero | `sldmodu 0x4c0ca000`, `0x4bb09f20`; confirmed static |

`ordinary_point` applies the native position setter and represents a two-dimensional ordinary point before segment use
`ordinary_line` represents its constructor before permanence and adjacency operations
These are deliberately separate from a family writer
They do not claim a complete sketch, dimensions, solver state, profile, or pad

`new_sketch` represents the native empty sketch constructor, including its managers
`new_profile` extends an allocated `moProfileFeature_c` supplied by the model factory
It binds a supplied `moCompRefPlane_c` node, constructs the empty sketch, and retains its owner link
Its profile cache is null and its raw dynamic storage is empty by the constructor rules above
This is an empty constructor graph, not a polygon-family emitter or an accepted document

## Contracts

Helpers use keyword-only semantic inputs and return `Core.Obj` nodes or typed field mappings
`DerivedFields` keeps authored and derived fields separate and refuses to replace a derived field
Endpoint references and handle references retain node identity
The archive serializer remains responsible for archive class and object indexes
No helper reads a file, saved record, table, oracle, or fixture at runtime

## Remaining construction

Origin/frame-point construction, dimensional parameter/tolerance/name/display links, post-insertion manager state, contour/chain construction, unit conversion, and extrude feature ownership remain required
The profile serializer address is `sldmodu 0x4bb1bdc0`
Null cached body has constructor/store/load evidence at `0x4c0ca000`, `0x4c254640`, and `0x4c253660`; this does not establish regeneration acceptance

## Verification

No local tests, imports, reproductions, or oracle calls were run
The edited Python source passed static AST syntax parsing without importing or executing it
Remote CI evidence will be recorded with the change
The success criteria remain unsatisfied until held-out generated files pass target opening, rebuild, geometry measurements, feature-tree inspection, and dimension editing between healthy controls
