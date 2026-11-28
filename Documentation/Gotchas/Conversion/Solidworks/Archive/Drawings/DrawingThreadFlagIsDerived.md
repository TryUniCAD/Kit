# Drawing thread flag is derived at save

The native `moModel_c` constructor seeds the cosmetic-thread cache to `1`. At save the full model scans its features and emits the resulting presence flag. The unlinked blank drawing emits `0` because it has no cosmetic thread features. Use the feature-derived value when generating this drawing. The lightweight reader uses the persisted cache. [Native constructor, predicate and serializer](../../../../../../re/solidworks/records/DrawingSaveBoundary2026.md#cosmetic-thread-presence)
