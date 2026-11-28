# Generate Fusion legacy appearance property streams

Kit's research property producer constructs the two logical property streams for an untextured `GenericSchema` appearance. The definition stream contains eight properties. The instance stream contains 40 properties, including 11 explicit absent-connection encodings. The producer uses the existing Fusion material value codec and takes its values from a grouped authored request.

## Use

Load `build_legacy_values(request)` from `re/Fusion/LegacyBodyAppearance/LegacyValues.py` with the checkout SDK on Python 3.14. Pass a schema `1` request with scope `legacy_generic_body_wire_values`. Supply all fields in the `definition`, `metadata`, `diffuse_tint`, `reflection_transmission`, `ambient_occlusion_edges`, and `emission_normal` groups. The internal call returns the definition and instance byte strings in that order. The instance string begins at its first named property. The [authored compatibility request](../../../../tests/Convert/Api/Fusion/LegacyAppearance/AuthoredRequest.json) shows all required inputs.

Use explicit floating-point values for stored scalars and all four RGBA components. Write `0.0` or `-0.0` to specify the zero sign. The producer retains these values without converting colour spaces or applying units to unannotated native scalars. The library and version values are explicit `research:` symbols for this wire scope. Provide an empty thumbnail list and empty exchange and swatch strings. Populated connections and additional inputs are refused.

## Native field evidence

The existing strict research reader and census decoded five pinned discovery files with zero fallback. Reading their actual Protein record chains and persisted public JSON recovered equal typed assets. The untextured records each contained eight definitions, 40 instance properties and 11 one-byte absent-link encodings. The M068 connected record used the same field inventory and carried two enabled bitmap connections. This evidence qualifies the field layout for the scoped offline tests.

## Verification

Three integration cases passed in 20.57 seconds. Fresh processes consumed only the independently authored request. The receiving codec used the declaration resolved from the separate pinned native control. It recovered all 48 ordered values, signed zero, and every absent connection. A glossiness-only edit changed its decoded field and preserved the definition stream. Eight invalid requests returned their expected errors without creating a result.

| Authored output | Bytes | SHA-256 |
| --- | ---: | --- |
| Definition and repeat | 180 | `bb666a02d8292e17db4fa9434bac50e2225d796b6a1e38faae12a79ce10db004` |
| Instance properties and repeat | 339 | `97eb31b30eddc89aed2425a014a8712d146f30bc22335dbc54f4292df0d41351` |
| Instance properties after glossiness edit | 339 | `d020fc5d9251baa162ff3fb815c56ac5ef3ea19c922b60e559d9147ac8bc4669` |

## Limits

The scope covers logical property streams. The two missing legacy schema declarations still require evidence for UI and renderer implementations, resources and catalog identity. A native legacy body has its own separate stored appearance and a modern compatibility partner. The physical aspect uses a third appearance instance. Those bindings, complete package generation and licensed Fusion acceptance remain open. See [legacy appearance resource connections](../../../Gotchas/Conversion/Fusion/Materials/FusionLegacyExternalResources.md).
