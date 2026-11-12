# Keep the empty configuration sidecar boundary

Kit still reads and writes only empty configuration sidecars.
A native attempt to make configured designs failed because of an account restriction.
Kit did not get native evidence for configuration tables, rules, rows or cells.

## Current behavior

| Member | Accepted content | Other content |
| --- | --- | --- |
| `DesignConfigurationTable.<GUID>.dsgcfg` | JSON object `{}` | `ValueError` |
| `DesignConfigurationRule.<GUID>.dsgcfgrule` | JSON object `{}` | `ValueError` |

`ReadConfigPart` raises `Nonempty Fusion configurations require a qualified schema` for a nonempty object.
`CheckDocConfig` checks each sidecar against its Design serializer trigger.
This change does not remove the pin, because no configured variant is qualified.

## Native attempt

The [configuration control script](../../../../re/Fusion/LocalOracle/LinksConfigs/CreateConfigControls.py) ran in Fusion 2706.1.17.
It made a part with a `lengthC` parameter, a body and a cut hole, and saved it to the acceptance project.
It then called `Design.createConfiguredDesign`.

| Step | Result |
| --- | --- |
| `C0_plain` export | 48,973 bytes, SHA-256 `ca0392bb9be055f2bdb06ed9dcbef4946d788ba31bb08b7677cc53f5e64b3590` |
| `Design.createConfiguredDesign` | `RuntimeError: 3 : Cannot create configuration top table as the user is restricted.` |
| Documents open at the end | 0 |

The script did not reach the steps for parameter columns, suppression columns, appearance tables, rows, rule creation or row activation.
[`LinkEvidence.json`](../../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json) records the sanitized result.

## Corpus check

`FindConfigs.py` scanned 1,063 F3D and F3Z files under `re/Fusion` and `examples`.
It found no configuration sidecar larger than 2 bytes.
The members of the example1 bundle contain `{}` in both sidecars.

## Next step

Run the control script again with an account that can create configured designs.
The script records an export after each table, row, cell, rule and activation step.

## Related information

- [Configuration licence gotcha](../../../Gotchas/Conversion/Fusion/Configuration/FusionConfigurationLicense.md)
- [External references change](../Assembly/FusionExternalReferences.md)
