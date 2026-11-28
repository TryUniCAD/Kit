# Custom component-name source control

PR #121 adds an independent native author/reopen protocol for occurrence names that differ from the cylinder dependency filename. It binds actual selected component IDs through the registered 2026 interfaces, checks both feature/component names, and requires complete trees, configurations, transforms, cylindrical references and analytic geometry through a child-first save and fresh reopen between unchanged D01 controls.

Use [the protocol record](../../../../../re/solidworks/records/CustomComponentNameSourceControl2026.md), [freezer](../../../../../re/tooling/sw2026/FreezeCustomComponentNames01.py), [observer](../../../../../re/tooling/sw2026/InspectCustomComponentNames01.py) and [host receipt](../../../../../re/solidworks/measurements/2026/CustomComponentNameControlHost01.json). Host verification passes for 41 frozen files, both 25-row expected trees and independent geometric predictions. Syntax and undefined-name checks pass.

The application name-update preference must already be false; the tool never changes it. Native source authoring, setter behavior and persistence remain pending. This source-control protocol adds no generated override database, production registration, held-out result or writer acceptance.
