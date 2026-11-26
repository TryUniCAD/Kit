# A saved P03 derivative can retain payloads without a public B-rep

The exact native-saved 12 mm P03 derivative completed the pinned SDK's strict default read with one design body and three current-schema Parasolid payloads. The returned document had `brep=None` and an empty diagnostic list. The design-body record contained bounds from the model summary. The separate native process measured the physical solid. Strict default on the original generated input had refused because it carried no readable Parasolid payload.

Check the returned `brep`, payload list and native measurement separately. Use the explicit model-only options for history-only inspection. The complete typed reader still refused `moSimpleSurfIdRep_c` schema 1 on this saved derivative. [Exact derivative read and command](../../../../Changes/Research/Encoder/SolidworksConstrainedBossNativeLifecycle.md)
