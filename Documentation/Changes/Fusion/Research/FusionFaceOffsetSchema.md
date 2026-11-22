# Signed face offset schema

The immutable `FaceOffset` feature definition retains one target body, one face selection and one live signed distance parameter. The wire type is `FaceOffset`; its fields are `target_body_id`, `face_selection_id` and `distance_param_id`. Import the type from `interchange.Features.Offsets.FaceOffset`.

The feature kind is `offset` and has no boolean operation or sketch operand. It modifies the persistent body named in its output IDs. The face selection path names that body and one physical B-rep face. Validation follows body-to-region-to-shell-to-face ownership, requires one explicit earlier body producer, and checks the owned distance parameter through the existing finite length-unit conversion boundary. Positive and negative lengths retain the same selected face; a geometry evaluator applies the sign along that face's outward normal.

The face-offset research CLI now emits this typed definition after resolving each source parameter and bound-face recipe. Six native controls, including two held-out cases, support the schema. A process-boundary compatibility replay checks source CLI output through the public wire registry and its independent native geometry comparisons. Tests were authored for remote execution and were not run locally.

This schema does not make native offset archives strict-neutral decodable. Native projector graph qualification, physical label and snapshot validation, geometry evaluation in production adapters and native output acceptance remain unfinished. Existing export restrictions stay enabled.

Actual CLI source analysis decoded all six modified archives to typed FaceOffset definitions with native geometry comparisons still passing. SchemaDecode.json records source and implementation hashes. Targeted Pyright, Mypy and repository steering checks passed for 15 Python files. Public document compatibility coverage includes a zero-distance offset over real stock topology and rejects broken parameter ownership, missing faces and missing prior producers; these checks await remote execution.

## Filtered reads and export qualification

A complete JSON or mapping input must supply the offset face topology. After validating that complete input, geometry filtering records `kit.omitted_brep` on the filtered view. Post-filter validation permits that intentional omission. Persisting the marker cannot make a missing-topology source input valid. Wrong B-rep field types produce the ordinary DocumentError instead of an attribute error.

FaceOffset definitions remain blocked at shared and direct writer boundaries until a production geometry evaluator is qualified. A valid semantic graph, including a signed distance, is not proof that a retained stock solid is its evaluated result. Public compatibility replays cover positive, negative and zero distance serialization, strict filtered JSON reads, absent or malformed source topology, forged omission markers and export refusal without stream mutation. These replays await remote execution.

Configured JSON reads use the same complete-input offset topology check before variant validation and geometry filtering. Filtered metadata remains immutable. Public document JSON and mapping serialization refuse an offset view whose B-rep was omitted; file serialization validates and encodes before creating directories or overwriting a file. Public configured-read and persistence replays cover forged omission markers, immutable view metadata and unchanged existing destinations. These tests await remote execution.
