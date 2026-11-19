# Distinguish cylinder and parent open warnings

Task B05-SW2026-CONCENTRIC, owner the PR #121 takeover agent. The frozen diagnostic reopened the existing generated feature child on its own and then loaded its unchanged generated parent. Both pristine native controls passed before and after. All four phases ran in separate SOLIDWORKS 2026 SP05.2 build 34.5.2.0604 processes. [Diagnostic receipt](../measurements/2026/GeneratedConcentricOpenDiagnostic01.json)

The standalone cylinder returns error 0 and warning 32. It has one visible solid, zero document problems and a clear NeedsRebuild property even before explicit rebuild. The exact cylinder geometry, both driving dimensions and feature tree pass both times. The save flag stays set and the update stamp moves from 104 to 118.

The parent also returns error 0 and warning 32 with the expected document type and path. Both occurrence IDs are unique and each resolves its one-solid child before and after a successful explicit rebuild. The parent's stamp advances from 103 to 104 and its own NeedsRebuild property stays clear. The neutral documents explicitly name the occurrences Cylinder-1 and Cylinder-2. COM returns NeutralCylinderAlphaDerived-1 and NeutralCylinderAlphaDerived-2. The strict capture therefore cannot pass its name-and-path condition. The mate geometry and edit/save lifecycle remain unmeasured. The standalone warning demonstrates that parent mate solving cannot account for every observed warning.

The diagnostic reads no sealed designs, preserves all inputs and measures no saves. The earlier zero-warning gate still applies. [First native comparison](../measurements/2026/GeneratedConcentricNativeOpen01.json)
