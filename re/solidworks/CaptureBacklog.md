# SOLIDWORKS and Fusion capture backlog

This is the live work remaining after the offline audits for the plan on PR #296.
Run each variation against a fresh saved control before and after. Preserve the
native save, reopened API inventory, build and case identity, worker receipt and
measurement logs. Keep holdouts out of discovery. For derived fields such as
topology and mass, record the change rather than attempting to hold it fixed.
If an authoring operation couples settings, record the coupling; do not describe
the capture as isolating a field. Offline re-decoding of an existing saved file
is not a new capture.

## First: restore trustworthy capture and editable sketches

| Work item | Author or run | Single variable | Holdout | Unblocks |
| --- | --- | --- | --- | --- |
| Missing retry evidence ([PR #370](https://github.com/TryUniCAD/Kit/pull/370)) | Recover the retry run directory or controller state before rerunning anything; recover native files, observations and failures together | Measurement stage: body vs sketch region, replayed separately on the same input once identified | An identified failed case excluded from diagnosis | Classification of the plan's failures; nearby Fusion counts are not the missing SOLIDWORKS run |
| COM/RPC recovery ([PR #370](https://github.com/TryUniCAD/Kit/pull/370), [PR #381](https://github.com/TryUniCAD/Kit/pull/381)) | Run a healthy catalogue recipe and induce session loss in an owned fresh process | RPC failure; independently exercise a retry that loses its session again | A different recipe; verify no additional retry on repeated loss and no dependent decoder release after failure | Live evidence for owned-process retry and host dispatch; does not qualify persistent owners |
| Shutdown recovery ([PR #381](https://github.com/TryUniCAD/Kit/pull/381)) | Capture and close the same recipe normally and with a stalled shutdown; exercise launcher and worker deadlines in separate pairs | Shutdown path | Different recipe with an unrelated interactive session left untouched | Live evidence for cleanup, retry receipts and separation from normal exit |
| Thin-wall side ([PR #370](https://github.com/TryUniCAD/Kit/pull/370)) | Re-author the corrected one-sided thin-wall recipe and record sketch regions and body measurements on reopen | Wall side in the local sketch frame | Opposite-facing sketch on another plane | Corrected authoring and region/body capture |
| P04 text placement ([PR #380](https://github.com/TryUniCAD/Kit/pull/380)) | Save a rectangle-only control twice; drag one dimension label without resizing | Label location | Other label on another plane | Display placement fields |
| P04 driving state | Save the same dimension as driving and reference | Driving state | Other dimension on another plane | State, cache and display binding |
| P04 operand attachment | Reattach one operand to an equally spaced point | Operand identity | Another equal-distance pair on another plane | Ordered handle references |
| P04 size edit | Edit one rectangle dimension and rebuild | Driving scalar | Other dimension on another plane | Coupled placement and value copies |
| P04 display tail | Add or edit a downstream feature on an otherwise unchanged rectangle; test termination separately | Downstream feature state or termination per pair | Different downstream feature | Tail word ownership independent of sketch size |
| P02 radial label ([PR #380](https://github.com/TryUniCAD/Kit/pull/380)) | Drag only the radial label of a dimensioned circle | Label location | Off-origin circle | Radial display placement |
| P02 radius ownership ([PR #373](https://github.com/TryUniCAD/Kit/pull/373), [PR #380](https://github.com/TryUniCAD/Kit/pull/380)) | Dimension separate circles at unequal sizes; edit each separately | One circle's diameter | Different circle order and diameter pair | Ownership of the extra scalar and display caches |
| Off-origin circle ([PR #373](https://github.com/TryUniCAD/Kit/pull/373)) | Save a dimensioned Front-plane circle away from the origin; vary each coordinate in a separate pair | One centre coordinate, fixed diameter | Different signed centre and different plane; P05 is not a typed circle holdout | Centre encoding independent of radial geometry |
| Circle units | Save the same physical circle under different display units | Display unit | Additional display unit on a different circle | Physical versus display-unit copies |
| Stored axis rows | Draw a skew line; constrain it horizontal or vertical in separate pairs; repeat on a skew rectangle edge | One added relation | Different edge/member order | Stored rows versus geometry-inferred horizontal/vertical constraints |
| Other relation codes | Use a no-relation sketch per recipe and add equal, parallel, perpendicular, concentric, tangent, symmetric, midpoint, collinear, fixed, normal, pierce or along-axis separately | One added relation per pair | New sketch and operand identities for each relation | Native codes, operand counts and row layout |
| Relation manager cache | Save a named relation absent and present; inspect the configuration cache and reopened API values | One relation | Different named relation and display units | Cache key and scalar units |
| Sketch-local coincidence | Make sketch-local points coincident without an origin operand; reverse selection order in a separate pair | Relation presence or operand order per pair | Different point identities | Handle ordering and trailer semantics |
| Native sketch acceptance | Open the generated rectangle or circle beside healthy native controls; individually edit a driving dimension | Driving value | Different plane and dimensions; do not recycle discovery files | Loadability, editability and geometric response |

## Next: dependent features and compound parts

| Work item | Author or run | Single variable | Holdout | Unblocks |
| --- | --- | --- | --- | --- |
| Boss direction ([PR #378](https://github.com/TryUniCAD/Kit/pull/378)) | Save a rectangular blind boss forward and reversed with fixed support and depth; record signed API vector and centroid | Reverse flag | Offset asymmetric profile | Direction and frame disambiguation |
| Boss frame | Save the same offset asymmetric profile on each principal plane with fixed depth and direction; record the full transform and transformed points | Sketch support plane | Other offset and plane | Sketch-to-model binding |
| Boss operation and scope | Save first boss then overlapping merge-on/off bosses; contrast a cut on an existing body separately; record persistent body IDs, scope, volumes and body counts | Merge or operation per pair; vary scope separately | Two bodies with a different eligible target | Create/join/cut and affected-body identity |
| Chamfer | Save an asymmetric distance-angle chamfer and a two-distance chamfer on the same edge; independently edit angle or second distance within its own mode | Mode or one second scalar per pair | Different angle and unequal distances on a different edge | Scalar interpretation and neutral projection |
| Variable fillet | Author a variable fillet with distinct station radii, then change one radius keeping its station fixed; change station location separately | One radius or station coordinate per pair | Different station order and unequal radii | Radius-to-point assignment |
| Revolve direction | Author a two-direction revolve and alter only its second angular extent | Second-direction angle | Asymmetric profile with a different axis orientation | Second extent, sign and end condition |
| Cut sweep references | Save a cut with fixed profile and path; rebind to an independently identified equivalent path, then vary profile or guide separately | One path/profile/guide reference per pair | Distinct path and profile on another support | Ordered cut-sweep references |
| Cut loft references | Save a cut with ordered sections and a guide; change one section binding or guide in a separate save | One loft reference | Different section count and guide geometry | Cut-loft reference roles and ordering |
| Piston Ring KF / OneLights / TwoLights | Inventory each native-only cut on fresh reopen; author a small counterpart for each and edit its cut definition while retaining the unchanged originals | One cut's bound input or termination per pair | Original corpus files and independently authored contrast; do not count the light variants as independent cut geometry | Definition and topology evidence for the native-only cuts |
| Pattern | Pattern an existing feature, then independently vary count, spacing and seed binding in separate saves | One pattern parameter/reference per pair | Different feature seed and patterned axis | Pattern generator and instance/feature identities |
| Mirror | Mirror a feature, then a body in a separate family; rebind the mirror plane on an otherwise unchanged model | One plane reference | Different plane and seed | Mirror references and body ownership |
| Multibody composition | Build separate solids and apply a scoped dependent feature; measure body identities, volume and centroid across an upstream edit and reopen | One scoped target or one upstream dimension per pair | Independently authored multibody part combining qualified features | Body linkage, topology and propagation |
| Native timeline payloads ([PR #378](https://github.com/TryUniCAD/Kit/pull/378)) | Independently change one light, folder membership, note or exploded state; inventory the actual API object, owner and members | One payload or membership per pair | Different owner/name and document | Actual state versus built-in datum, folder and timeline placeholders |

## Next: manufacturing and other tree families

The offline inventory found sheet-metal master placeholders without resolved
payloads, no weldment or mold feature examples, and native-only advanced holes
and cut lofts. Boss lofts and boss/cut sweeps exposed their kinds without
parameter bindings. These are capture targets, not evidence of native support.
For each row below, independently author the holdout rather than cloning the
discovery file. Reopen it and record the same API fields, persistent selections,
and applicable body or feature measurements as for the pair.

| Work item | Author or run | Single variable | Holdout | Unblocks |
| --- | --- | --- | --- | --- |
| Sheet thickness | Save a base flange and edit its sheet thickness; keep bend radius explicit and fixed. Record thickness and body measurement | Sheet thickness | Different sheet outline and thickness | Thickness ownership beyond the master placeholder |
| Bend radius | Save the sheet with an explicit bend radius and keep thickness fixed. Record the radius and the resulting bend geometry | Bend radius | Different bend edge and radius | Radius ownership and independence from thickness |
| Flange angle | Add an edge flange with fixed length, radius and relief; record the signed angle and flange orientation | Flange angle | Flange on a different edge with another angle | Angle binding and sign |
| Flange relief | Change the relief type with other settings fixed; make a separate pair for each exposed relief dimension. Record type, dimensions and affected edge | Relief type or one relief dimension per pair | Another flange corner and relief geometry | Relief enum and dimensional ownership |
| Fold state | Save a folded sheet and its flattened state in the same configuration without changing its bend definitions. Record active state, suppression and body extent on reopen | Fold state | Different bend layout with an independently authored flat state | Flat pattern state and fold correspondence |
| Weldment profile | Apply a structural member to a fixed sketch and reselect the profile; record profile identity, section and member paths | Profile selection | Different profile family and sketch path | Structural member profile binding |
| Weldment trim | Trim the same members and change one trim operand with other settings fixed. Record ordered members, trim reference and resulting lengths | Trim reference | Different joint and selected target | Trim ownership and reference order |
| Weldment cut list | Move one body between otherwise unchanged cut-list groups; record persistent body IDs and group membership after reopen | One body membership | Another weldment with independently grouped bodies | Cut-list membership rather than inferred grouping |
| Mold pull direction | Use a drafted source solid with separately selectable direction references; record the resolved pull vector and classified faces | Pull direction reference | Different source part and pull axis | Direction binding and face classification |
| Mold shutoff | Keep pull direction and other openings fixed; change one opening's shutoff selection. Record the selected boundary and generated surface | One shutoff reference | Different opening topology | Shutoff membership and generated surface ownership |
| Advanced-hole stages | Build an advanced hole with unequal stages and edit a single stage diameter or depth in each pair. Record ordered stages, types and dimensions on reopen | One stage dimension | Different stage order and dimensions | Stage parameter ownership and order |
| Loft section profiles | Save a boss loft, and separately a cut loft on a fixed solid; rebind one ordered profile. Record section IDs and order on reopen | One section reference | Different section count and geometry for each operation | Ordered profile binding independent of the guide reference |
| Loft end constraints | Keep section order and guides unchanged; vary one start or end condition, then vary magnitude in a separate pair when applicable. Record end settings and their references | One end condition or magnitude per pair | Different end condition and section support | End constraint mode and parameter ownership |
| Sweep twist | Save boss and cut sweeps with fixed profile and path; vary twist mode or its amount separately. Record twist settings and resulting orientation | Twist mode or amount per pair | Different path curvature and twist value for each operation | Twist parameter binding beyond the typed kind |
| Cosmetic-thread size and depth | Save a cosmetic thread on a fixed bore; edit the thread designation and termination depth in separate pairs. Record the API designation, depth, termination and referenced face | Thread size designation or depth per pair | Different bore and thread designation with finite depth | Thread parameter meaning and feature attachment |

## Then: document state, assemblies and drawings

| Work item | Author or run | Single variable | Holdout | Unblocks |
| --- | --- | --- | --- | --- |
| Configuration selection | Save named configurations with distinct dimensions; switch the active configuration without altering saved overrides | Active configuration | Different configuration hierarchy and values | Switch/reopen behavior and saved identities |
| Configuration suppression and overrides | In a named non-default state, toggle one feature or edit one driving override in separate pairs | Suppression bit or one override per pair | Dependent feature in an independently authored derived configuration | Scoped state and derived geometry |
| Properties | Extend the literal-text control with linked/evaluated, typed or configuration-scoped values; test each separately | One value, link, type or scope per pair | Same property name with unequal values in separate scopes | Property ownership and evaluated-vs-literal semantics |
| Equations and external links | Save a driving equation or a linked reference, then edit one expression or retarget one file in separate pairs | Expression or reference target per pair | New equation or dependency graph | Reopen and propagation, not just saved strings |
| Material | Assign a physical material and vary assignment independently at part, configuration and body scopes; record density, mass and appearance | One material assignment per pair | Different material on a different body/configuration | Physical material versus labels/appearance |
| Assembly references and occurrences | Save a small local assembly of reusable components; vary occurrence transform, reference path or component configuration in separate pairs | One transform, path or configuration | Nested assembly with repeated instances and independently relocated files | Reference resolution and occurrence identity |
| Assembly mates | Add one mate per family, then edit a driving mate value; record persistent selections and motion on reopen | Mate presence or one driving value per pair | Different component geometry and mate operands | Solver binding and target load/rebuild validation |
| Drawing sheet and views | Save a linked part drawing; add a view or edit its orientation/scale in separate pairs; author assembly drawing separately | One view attribute per pair | A different view type and independently authored assembly drawing | Native drawing inventory and view projection |
| Drawing annotations and links | Add a linked dimension or annotation, then edit the referenced model and reopen the drawing | One annotation binding or referenced model dimension per pair | New link on another sheet | Associativity and propagation |
| Compatibility | Save the same measured recipe in each claimed vendor release; qualify additional catalogue features separately | Vendor build, or one recipe feature per pair | Independent native file per claimed combination | Version-specific load/edit/rebuild bounds |
| Fusion native acceptance | Reopen a generated Fusion candidate between healthy native controls and edit one qualified driving value; preserve independent observation | One driving value | Separately authored Fusion source and build | Live Fusion edit/rebuild evidence; malformed snapshot replay and captured projection failures remain offline work, not automatic requests to recapture |

See [Later-phase offline coverage](LaterPhaseCoverage.md) for the observed boundaries.
