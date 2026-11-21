# Carrier writes still account for every source capability

`WriteResult.dropped` can describe a loss, and write options can permit a carrier. The registry still requires all declared and inferred source capabilities to transfer. `CheckTransfers` raises `CapabilityLossError` for any reported drop before the path staging layer publishes the result. An admitted SOLIDWORKS geometry-only import transfers `brep` and `configurations` because those are the capabilities of its actual input.

Keep the original model and any scoped geometry projection available to the research diagnostic. Record omissions against the intact input. The projected import's successful result accounts for the projection's capabilities. [Write policy](../../../../src/convert/adapters/base/WritePolicy.py) · [Imported-body evidence](../../../../re/solidworks/records/ImportedBodyFallbackBoundary2026.md)
