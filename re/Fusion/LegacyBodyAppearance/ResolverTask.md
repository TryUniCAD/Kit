# A05c Fusion legacy resource resolver evidence

| Registration | Value |
| --- | --- |
| Task | `A05c-FusionLegacyResolverEvidence20261126` |
| Owner | Fusion encoder swarm worker 3 |
| Status | Static alias evidence recorded. Runtime dispatch and catalog lookup remain open. |
| Delivery | Separate normal dependent branch from [PR #344](https://github.com/TryUniCAD/Kit/pull/344) at `b83d253b1876d027655e79384058ebd5b9a0dda5`. Dependent evidence delivery pending. |
| Dependencies | [Legacy property streams](Task.md), the pinned Fusion 2706.1.17 build, the archive comparison and the existing local analysis provider. |
| Owned outputs | This task page and its scoped semantic evidence. Private licensed-analysis database outside Git. |
| Exit | Attribute the legacy schema and its resources to an exact module and semantic consumer. Keep catalog identities, package resources, body and physical appearance roles, and absent or unresolved targets distinct. Report evidence for each supported rule. Preserve open runtime and descriptor acceptance criteria. |

## Candidate build

Fusion 2706.1.17 launcher SHA-256 `2cbbbc14ab4dd4dd40c21ba85861317d2d6f532abbc1b71c37835e22e7090abc`. This identifies the installed deployment. The following candidate module identities are required to interpret static observations. Ownership remains unqualified until relevant vocabulary and references are observed.

| Candidate | File version | SHA-256 |
| --- | --- | --- |
| `atf_protein_material.dll` | 15.17.0.0 | `7415333dead109e83d7c64ced97b1fceec6ecbca5a965ec97518e363844bd322` |
| `OGSProtein.dll` | 17.1.5.0 | `4034d8f08755ff127efa6af14f4bf76eec10a8b9722743e08d07177f922fc04b` |
| `AdMaterialUI.dll` | 6.0.1.2 | `98d2c23e923cc7dfae9a650f8d31d3fefdeb1081a639994380085cafde4e96d7` |
| `adp_core-6_1.dll` | 6.0.1.1 | `0eb34ae559e8d25c650be132e8ea6a44a3361f582dcb098cff3de177fd5db48c` |
| `adp_data-6_1.dll` | 6.0.1.1 | `1a24fae5457c35cc2603eadff638718f4a4e7da1520ca358418ea45801508413` |
| `adp_service_opczip-6_1.dll` | 6.0.1.1 | `38fef9ec2aca828ec2e1d0c8321cef9b2b95269d44d497a170078390e4eafb8f` |
| `adskassetapi_new-16.dll` | 5.0.2.1 | `9e185ecc157c129667d54242614381a7bdc2af3932a5ef005b15d780c0337b8c` |

## Scope and evidence boundaries

The existing local REA 6.7.0 script and Ghidra 12.1.2 can provide static evidence. Identify candidate ownership using the schema, material field and package reference vocabulary already present in the pinned archive controls. Use a private, separate analysis project. The installed files, private databases and detailed listings stay outside Git. Only semantic conclusions and hashes enter evidence.

The nested Protein package `f1253b0a590030e44d8b06e8ffce60712ecbf370fcf63830d330d46a116a359c` identifies one observed resource-bearing specimen, preserved by two bundles. Its six exact thumbnail references point to their own `AssetCore.Identifier`, appearance instance directory, role slot and linked PNG. Eleven other Generic definitions in the same package name a `Mats/Generic` thumbnail without an archive member. This locates embedded ownership and leaves external namespace lookup unresolved.

The scope omits Fusion execution and keeps current descriptor, source and native output guards. A static call path cannot establish which branch a licensed application actually uses or qualify rebuilt candidates. The prior application-tool block and native-only acceptance remain open.

## Observed static lookup behaviour

Only the candidate `adskassetapi_new-16.dll` held both schema names, the numbered material property stream names, the material library and version keys, the UI and renderer keys and `_Post2015`. Cached REA 6.7.0 and Ghidra 12.1.2 confirmed the exact build fingerprint above and nine references to `_Post2015`. Eight references belong to three procedures and the remaining reference is a data pointer. The two small lookups each query the exact base and suffixed keys separately from the same material container.

| Condition in the two inspected lookups | Static result |
| --- | --- |
| Exact base missing, with or without a partner | The lookup yields no selected asset. |
| Exact base present, partner missing | Both paths return the base result. |
| Exact base and partner present in the first lookup | The base result remains selected. |
| Exact base and partner present in the second lookup | The partner is selected in caller mode `2`. The other branch keeps the base. |

Both lookups had data references and no resolved direct code caller. This static result leaves the caller mode during document open unresolved. The existing Kit strict reader's suffix preference remains an SDK behavior. Historical native open and reopen measurements of intact pairs show the effective modern appearance for those cases.

An inspected `AdvancedUIDefinition` use checks the type of a named entry. An inspected `ImplementationOGS` use registers the lookup key. The parent schema name appears in schema initialization. These observations identify selection and validation boundaries. The runtime resolution and requiredness of the `Mats/Generic` UI, implementation and logical thumbnail paths need separate evidence.

The private evidence index has SHA-256 `37f89a34090bcd787ff0be4dc25424604c8ef03f205afc5696c85d7faf1c938b`. The indexed first and second lookup receipts have SHA-256 `1a66f48580a57b6c04d47c57036f1ce069873c25df94621ce471aa7a49028daa` and `c03a58c8b737f6e599b029c816a06fffb82de1063cacd75a21c58334b9a147ac`. Both isolated provider sessions closed. No Fusion application ran. No loaded appearance, writer or native acceptance is claimed. See the [appearance lookup gotcha](../../../Documentation/Gotchas/Conversion/Fusion/Materials/FusionAppearanceLookupMode.md).
