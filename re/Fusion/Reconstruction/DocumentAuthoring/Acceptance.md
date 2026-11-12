# Independent document acceptance

This addendum supersedes the empty candidate's original pending-acceptance
status in `README.md`. The frozen generation artifacts remain unchanged.

The complete independently authored parameter F3D was accepted by Fusion
2706.1.17. The native report is
[`ParameterBrowserAccepted.json`](../../LocalOracle/Authored/ParameterBrowserAccepted.json).
The accepted archive SHA-256 is
`f6e92a059e3e9db0c914f93b17191d6019fc34b5cd321e97ee83a3c75ab813c6`.
The package combines this directory's semantic Design writer with independently
authored ACT, Browser, manifest, asset, and ZIP layers.

Native opening returned a parametric design with millimeter display units,
`authoredLength = 17.25 mm`, and no sketches, bodies, or timeline features.
The parameter changed to 31.5 mm, saved, and reopened with that value. Fusion
then created a radius-20-mm circle and extruded it using the authored parameter.
The resulting native document had two timeline features, one sketch, one solid,
three faces, healthy feature status, and volume
39.5840674352331 cubic centimeters, matching `π·2²·3.15`.

This establishes that the constructor-empty material state, absent render
settings, empty named views, single mm/MKS unit system, zero invalid-cache
timestamp, and newly allocated Design identities are sufficient for this
document profile, including subsequent native modeling. The native feature
creation portion is validation of the authored document foundation; it is not
acceptance of the separately authored circle/extrusion feature variants.

The initial package attempts exposed independent container/Browser problems:

- Explicit ZIP directories and the required BRep blob folder are used by native
  segment/blob initialization even when no BRep part exists
- Primary offsets must increase in entity-ID order; the ACT writer initially
  emitted fresh identities out of order. `Variants/BulkOrdering.json` contains
  the exact native tree traversal and rejection evidence
- The Browser's relationships entry requires an `AssyConstraints` object, not
  the separate `Relationships` collection. The wrong declared target class
  survived graph loading and crashed during viewport activation

The Browser fix changed its semantic target to authored `constraints` identity
1022. This Design candidate did not need a render/default-material workaround.
The absence of render settings was therefore not the cause of the crash.

The receiving application's import names the root `Untitled`; that behavior
does not indicate a lost parameter or missing component. Save/reopen and the
subsequent feature result are bound to separate native-output hashes in the
report. Production promotion still needs repository integration checks and the
same qualified format/target-application acceptance boundaries.
