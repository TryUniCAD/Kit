# Automatic body scope has runtime state

The ordinary cut stores the scope word `f544`. The separate automatic
selection word at runtime offset `+0x558` has no standalone field in the
ordinary body-feature archive. Native authoring initially sets auto scope
with an empty selected-wrapper array. A successful merge materializes its
actual body references and clears the runtime selection word.

Treat the constructor state and the load state separately. Verify how the
concrete feature restores automatic selection or resolves explicit targets
before relying on an empty saved body array. The pattern loader's restore
condition belongs to its own serializer.
[Ordinary blind-cut lifecycle](../../../../../../re/solidworks/records/OrdinaryBlindCutConstruction2026.md#native-creation-and-body-selection).
