# A thin-revolve solid cache does not qualify editable history

Two independently authored SOLIDWORKS 2026 thin-revolve files contain an active Parasolid partition. Both legacy reads exposed the solid and some dimensions while leaving the actual thin walls untyped. The linked archive reader stops at the saved linked-atom class before it can reach the wall owners.

The strict inspection refuses this partial state in both full and design-only modes. Explicit non-strict inspection retains the available native geometry and metadata. Raw extraction can still return the ordinary partition payloads. [Pack-bound saved and generated observations](../../../../../../re/solidworks/measurements/2026/SdkThinReadReviewRecovery01.json)
