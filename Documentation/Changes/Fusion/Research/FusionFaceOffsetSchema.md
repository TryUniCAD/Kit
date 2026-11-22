# Signed face offset schema

The immutable `FaceOffset` feature definition retains one target body, one face selection and one live signed distance parameter. The wire type is `FaceOffset`; its fields are `target_body_id`, `face_selection_id` and `distance_param_id`. Import the type from `interchange.Features.Offsets.FaceOffset`.

The feature kind is `offset` and has no boolean operation or sketch operand. It modifies the persistent body named in its output IDs. The face selection path names that body and one physical B-rep face. Validation follows body-to-region-to-shell-to-face ownership, requires one explicit earlier body producer, and checks the owned distance parameter through the existing finite length-unit conversion boundary. Positive and negative lengths retain the same selected face; a geometry evaluator applies the sign along that face's outward normal.

The face-offset research CLI now emits this typed definition after resolving each source parameter and bound-face recipe. Six native controls, including two held-out cases, support the schema. A process-boundary compatibility replay checks source CLI output through the public wire registry and its independent native geometry comparisons. Tests were authored for remote execution and were not run locally.

This schema does not make native offset archives strict-neutral decodable. Native projector graph qualification, physical label and snapshot validation, geometry evaluation in production adapters and native output acceptance remain unfinished. Existing export restrictions stay enabled.

Actual CLI source analysis decoded all six modified archives to typed FaceOffset definitions with native geometry comparisons still passing. SchemaDecode.json records source and implementation hashes. Targeted Pyright, Mypy and repository steering checks passed for 15 Python files. Public document compatibility coverage includes a zero-distance offset over real stock topology and rejects broken parameter ownership, missing faces and missing prior producers; these checks await remote execution.
