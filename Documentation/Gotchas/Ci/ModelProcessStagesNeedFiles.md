# Model process stages need focused files

Splitting an embedded process into short constants does not satisfy the
declaration-splitting rule when independent construction, serialization and
parsing stages still share one module.

The model process review identified `KBaseGraph`, `KBaseStreams` and `KBaseLoad`
as separate responsibilities. Each generated stage now lives in its own
focused module under `tests/convert/solidworks/research/Model/`.
`ModelProgram.py` composes their exact symbols in the established order;
`ModelBuilderProcess.py` owns the isolated subprocess launch.

Preserve the concatenated program text while moving stages. The extraction's
static comparison retained SHA-256
`23d3aeb06e82ede7468f7dae3ced1b789a0fcd059a30a9e0f04869b371160ecb`.
The trusted initialization and strict construction-audit boundary therefore
remain in the same program positions. The subprocess still requires remote
integration execution after the refactor.
