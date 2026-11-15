# SOLIDWORKS 2026 profile construction

The research builder constructs fresh polygon profile graphs from semantic vertices and constructor-backed format rules
Endpoint and handle indexes derive from node references when the archive schema reads the fields
The helpers contain no saved-record defaults or runtime file reads

Use `re/tooling/sw2026/builders/Sketch.py` with `re/tooling/sw2026` and its `serial` directory on the Python import path
All helper inputs are keyword-only
`ordinary_point` constructs a positioned ordinary 2D point
`ordinary_line` constructs an ordinary line from point nodes
`line_handle` refers to a line node in its owning array
`PlaneFrame` and `frame_transform` convert an authored orthogonal frame to native transform fields
`new_sketch` constructs native empty sketch collections and managers
`new_profile` binds that empty sketch to an already allocated profile feature and a plane-reference node
`closed_profile` adds a validated closed ring with any number of at least three vertices
`origin_profile` constructs the document origin's point and logical constraint graph
`NodeOrder` keeps geometry references symbolic and computes its index map once when emission reads a field
Counts derive from the current collections
An exact rational sweep with a balanced active tree validates intersections in `O(n log n)` comparison work
It rejects nonadjacent touches and adjacent backtracking overlaps while retaining the authored f64 coordinates

`Extrude.py` constructs native blind end specifications and their live dimensional graph
`live_blind_extrusion` takes an allocated extrusion body feature, a constructed polygon profile, authored depth, shared ID allocator, design-intent boolean and explicit selected-leader presentation value
It constructs two length parameters and two zero draft-angle parameters with names `D1` through `D4`
It also retains the native transient zero-length `D19` from-offset graph and its real allocated ID, even though blind type zero omits that display from storage
Each parameter has its own feature dimension, local handle and display/text graph
It attaches the native end specification and profile dependency to the feature
The returned `ExtrusionGraph` retains those node references and reports its current forward parameter value
Missing handles, mismatched driving values and unsupported depth/draft inputs cause explicit construction errors
Lengths below `1e-14` metres fail because the native dimension constructor clamps them to zero
The shared `Model.py` factories supply the node and component-reference base fields
Dimension allocation binds directly to serialized `f50`, using the shared field-aware allocator

Display construction uses the native null-document constructor branch and explicit design-intent input
It does not copy document annotation style or session preferences
The native constructors do not initialize serialized `SelLeader`, so the builder requires that value and has no default
A semantic no-selection value or independent neutral-value proof remains outstanding

These helpers are intermediate research
The vertex-only profile contract contains no authored sketch dimensions or constraints
It does not preserve a source sketch that contains additional design intent
The origin graph explicitly records that its post-constructor sketch update remains unresolved
It applies the proved post-origin `setNeedsUpdate(0,1,null)` mask to that origin node; the owner lifecycle remains the model composer's responsibility
The local inter-component-reference flag is now derived from the native update predicate; final solver status and modification-stamp delta remain unresolved for both polygon and origin graphs
Static native dataflow also closes local dependency-bit clearing, point-cleanup preservation and the status-to-colour mapping
The actual solver status remains a required dependency rather than a value inferred from the constructor
Native serializer keys identify entity `f38` as line type, independently from constraint status `f34` and sketch saved status `f128`
Further static control flow excludes the separate model-reference stamp increment for the supported local graphs; solver coordinate deltas and resulting statuses still require native observation
The construction ledger now audits the native runtime schemas of 19 class types named by the sketch and dimension builder layer, including the inline-only logical constraint that emits no class header
The dimensional graph requires the explicit presentation input and completed shared model graph
They do not change adapter capabilities
See [the construction evidence](../../../re/solidworks/records/ProfileConstruction2026.md) for binary addresses, confidence labels, contracts, and remaining fields
The [instruction-boundary gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/DisassemblyEntryPoints.md) records a disassembly failure found during this work
The [leader-selection gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/UninitializedDisplayLeaderSelection.md) records the unset serialized display field
The [unit-vector gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/DefaultUnitVectorIsZero.md) records the native zero-vector constructor
The [entity line-type gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/EntityLineTypeField.md) records the adjacent fields' distinct roles
The [process-program declaration gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/ProcessProgramDeclarations.md) records the focused-file rule for generated test programs
The [runtime-offset owner gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/SketchAndProfileRuntimeOffsets.md) distinguishes sketch solver fields from equal offsets in the separate profile object
The [base-tip gotcha](../../Gotchas/Ci/ProcessChecks/PullRequestBaseTip.md) records a stale PR base snapshot encountered during integration

No local tests or oracle measurements were run
The Python source passed static AST syntax parsing without imports or execution
All five existing polygon process cases passed in [native job 132714706575](https://github.com/TryUniCAD/Kit/actions/runs/43682093985/job/132714706575) for PR head `4cb6785739079d6ebe1b745a21a8e63e49862b2d`
That job passed complete fresh-part and shared model construction, reporting 138 passes and 158 skips in 40.09 seconds
That snapshot includes the origin-node lifecycle mask and model codec repair
New process integration coverage writes fresh sketch and blind-end object archives into a container, decodes them, checks reference and byte identity, then edits the live forward parameter and re-encodes it
Its geometry cases include variable vertex counts, a 10,000-line ring, crossings, touches, vertical overlaps, backtracking and valid collinear vertices
The 65,537-line case subsequently passed in [native job 132723081423](https://github.com/TryUniCAD/Kit/actions/runs/43684854129/job/132723081423), which passed all six polygon cases and failed only in separate inherited assembly parsing
It verifies dimension allocation and uses the shared `BuildAudit` guard before builder/schema imports, without a filename-suffix escape for direct data reads
The process stages each own a focused module under `tests/convert/solidworks/research/Polygon/`, while the small program composition and subprocess entry point import their exact declarations
Profile gotchas are grouped under `Documentation/Gotchas/Conversion/Solidworks/Profile/` to keep both parent directories within their file limits
The naming and directory repairs passed at head `ee2eed2e4732e995fb8b0a7b281b8834cdf9a7f6`
[Native job 132729524301](https://github.com/TryUniCAD/Kit/actions/runs/43687022248/job/132729524301) again passed all six polygon cases; its only failure was the next missing schema in inherited assembly resolved features
The process declarations now include the mandatory rationale comments authorized for these checks; their code and embedded programs are unchanged
The component sketch archive uses a seeded external profile owner and does not establish complete part-file acceptance
Held-out native acceptance, rebuild, body measurements, and dimension edits remain unverified
The first complete parent-generated H3 candidate failed native opening with an RPC error between two passing fresh controls
The subsequent native schema probe isolated its first rejection to the shared journal schema, before the hooked sketch serializer; the shared repair does not establish acceptance of later generated graph state
