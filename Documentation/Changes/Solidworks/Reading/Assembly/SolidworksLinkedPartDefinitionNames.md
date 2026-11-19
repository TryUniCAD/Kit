# Read the owned name of a linked SOLIDWORKS part

In a SOLIDWORKS 2026 assembly with one resolved external part definition, the reader uses the owned part filename stem when the component index repeats the parent filename stem in both model labels. The part must be a direct nonvirtual component, and its resolved document filename must agree with the indexed file. Occurrence names still come from their own reference rows. A distinct stored definition label remains authoritative.

Through `convert.open_document`, find the part in `document.assembly.definitions`. Its `name` is the human-readable linked definition label. The saved component-index `swName` is available in `definition.attributes["native_attributes"]`. Disabled or failed resolution follows the existing read behavior.

Sixteen fresh guarded SDK reads compared the prior and corrected projections. The two disclosed D01 modes and the generated component-index case changed only the affected label and its derived source seal. The distinct-label controls and missing-source behavior matched exactly. [Read guide](../../../../Reference/Adapters/SolidworksConcentricReading.md) · [Evidence](../../../../../re/solidworks/records/ConcentricDefinitionNames2026.md)
