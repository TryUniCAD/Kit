# Generated blind-pocket discovery parts

Add a research-only `blind_cut_discovery` request to the SOLIDWORKS 2026 part constructor. Supply a Front Plane rectangular blind boss and the pocket's circular centre, radius, depth, dimension text point, sketch and feature names, and explicit body scope. The composer adds the pocket profile, a fixed-centre radial dimension, and an instant-extrusion cut with its own driving depth. The cut and boss share the part allocator and archive machinery.

The two discovery choices start with absent selected-body, consumed-body and chooser records. `all_bodies` writes the all-bodies scope word. `empty_feature_scope` writes feature scope with no selected targets. These choices allow a controlled comparison of cold rebuild behaviour. [Construction and verification plan](../../../../../re/solidworks/records/OrdinaryBlindPocketSynthesis2026.md).

Both generated requests passed the guarded process comparison and eight linked stream round trips each. Three existing part, revolve and rectangle process checks also passed locally. The donor scan of `src` was clean. [Process evidence](../../../../../re/solidworks/measurements/2026/GeneratedBlindPocketProcess01.json)

The all-bodies part passed native open and rebuild with one solid and correct geometry to six significant figures. Empty feature scope produced warning 32, cut error 71 and the uncut solid. Both controls passed. Driving edits, saved reopen and held-out acceptance remain pending. The public SOLIDWORKS adapter remains read-only. [Native measurement](../../../../../re/solidworks/measurements/2026/GeneratedBlindPocketNative02.json)
