# Assembly light members need keyword rows

An assembly can contain all four lights under its actual Config-0 environment folder while the normal metadata reader omits the four feature rows. The separate KeyWords index must contain one flat row per actual light ID. The two measured types are `Ambient` and `Directional`.

Build those index rows from the actual environment objects. Preserve their binary nesting and require unique IDs across the root and member rows. [D01 source and re-emission evidence](../../../../../re/solidworks/records/ConcentricParentLights2026.md)
