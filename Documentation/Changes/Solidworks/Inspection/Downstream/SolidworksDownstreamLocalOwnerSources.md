# Ordinary downstream local-owner source proof

PR #121 adds a reproducible source-only record for the exact 2026 standalone `moUnitComponent_c` owner wire and the ordinary boss surface keeper's `moFR_c` file/configuration reference.

The [record](../../../../../re/solidworks/records/DownstreamLocalOwnerContext2026.md) distinguishes the runtime actual model from the standalone null owner tag and read-side rebind. It also derives the external-list index allocator and the separate active-configuration update under partition rollback. The local zero-connection object remains distinct from a header self-file record.

Use `re/tooling/sw2026/downstream/VerifyLocalOwnerSources.py --bin-directory <licensed-modules> --record <record-json> --output <unused-receipt>` to repeat the source check. The [measured host receipt](../../../../../re/solidworks/measurements/2026/DownstreamLocalOwnerSource01.json) verifies eight original images, 67 complete function entries, 99 intervals and 11 actual virtual targets. No vendor bytes or listings are included.

This is format evidence, not a writer activation or native cache qualification. Native processes, SDK product executions, CAD input reads, held-out reads and VM calls were zero. Other owner masks, database serialization, external components, older versions and mutated runtime rollback state remain outside this selected ordinary profile.

See [standalone owner rebinding](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/StandaloneUnitOwnerIsRebound.md) and [index/configuration distinction](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/ExternalReferenceIndexIsNotConfigurationId.md).
