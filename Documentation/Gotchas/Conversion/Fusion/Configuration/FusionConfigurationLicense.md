# Configured designs need an unrestricted account

## Expectation

`Design.createConfiguredDesign` makes a configuration top table for a saved parametric design.

## Actual behavior

Fusion 2706.1.17 raised an error for a saved part in the acceptance project.

```text
RuntimeError: 3 : Cannot create configuration top table as the user is restricted.
```

The API call is available, but the account cannot use it.
The design stays an ordinary part.
Its configuration sidecars stay empty JSON objects.

## Workaround

Use an account that can create configured designs.
Do not take empty sidecars from an unconfigured design as evidence for configured designs.

## Evidence

- [Configuration control script](../../../../../re/Fusion/LocalOracle/LinksConfigs/CreateConfigControls.py)
- [Sanitized result](../../../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json), key `configuration`
- [Configuration boundary change](../../../../Changes/Fusion/Configuration/FusionConfigurationBoundary.md)
