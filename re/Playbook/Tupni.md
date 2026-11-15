# Tupni-guided format recovery

Use this workflow when the vendor loader is available and manual schema recovery
has reached repeated unknown fields, variable records or indirect dispatch. Read
the [CAD success criteria](../../Documentation/Reference/Operations/CadSuccessCriteria.md)
and this book's [loader](LoaderAnalysis.md), [corpus](GenerativeCorpus.md) and
[writer](WriterModel.md) chapters first. This method adds evidence; it does not
relax acceptance.

## Source and adaptation

Source: Weidong Cui, Marcus Peinado, Karl Chen, Helen J. Wang and Luiz Irún-Briz,
*Tupni: Automatic Reverse Engineering of Input Formats*, ACM CCS 2008,
pp. 391–402, DOI 10.1145/1455770.1455820.
[Primary paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tupni-ccs08.pdf).

Tupni analyzes how a parser consumes input: operand accesses identify fields,
iteration-dependent loops expose record sequences, handler instruction sets
identify record types, and symbolic predicates expose constraints. It combines
results across inputs. Its coverage depends on exercised paths; unread bytes and
sample-specific predicates remain limitations. See §§3.3–3.9 and 7.

Kit applies those ideas to native CAD archive recovery. This is an adaptation,
not a claim to have installed or reproduced the paper's original prototype.

## Choose an observable boundary

Start where the loader consumes meaningful archive bytes. For compressed CAD
containers, identify both the container decoder and the decompressed stream
buffer. Assign a distinct input identity to each stream and preserve its digest.
Compressed-file offsets and decompressed-stream offsets are different coordinate
systems. Never join them without a measured mapping.

Recover archive primitive readers, object/class dispatch and collection loops
from the exact target build. Record the DLL digest and relative virtual address
for every hook. Resolve runtime module bases on every launch; do not hook a
preferred-image address as if ASLR were disabled. Verify architecture and realm
before touching the target, especially for emulated x64 CAD on Windows ARM64.

Use bounded, read-only observation hooks. Do not change return values, model
memory, validation branches or loader errors to make a candidate pass. Detach
hooks in cleanup. Keep instrumentation runs separate from clean acceptance runs.

## Preserve the authority of each observation

| Label | What the evidence establishes | What it cannot establish alone |
| --- | --- | --- |
| Native instruction trace | Executed instructions, byte provenance and supported operand dependencies | Unexecuted branches, ignored fields or unsupported instruction semantics |
| Native API boundary trace | Actual primitive/object calls, runtime arguments, cursor movement and call sites | Complete instruction-level taint or every field dependency |
| Static native dataflow | Recovered operations and possible dependencies in shipped code | That a branch executed for an input |
| Kit codec trace | Which implemented schema paths consumed source bytes | That Kit's schema matches every vendor path |
| Corpus correlation | Which observations co-vary across authored inputs | A universal formula or constant |

A trace manifest must name its label. Never relabel an API hook log or a Python
codec log as an instruction-level taint trace. Preserve failed captures and
explicitly state dropped events, unsupported instructions and truncated ranges.

## Record a reusable trace contract

Each capture needs these identities and measurements:

| Group | Required contents |
| --- | --- |
| Target | Application build; every observed module's SHA-256, architecture, runtime base and size |
| Tool | Version, executable/package digest, hook-source digest, selected process and realm |
| Input | Source hash, neutral authoring spec, stream identity, decoded size and digest |
| Event | Sequence number, thread, module/RVA, event kind, call/loop scope and input ranges |
| Value flow | Input-byte provenance, operand width/type/order, operation and destination; unsupported semantics stay unknown |
| Boundaries | Cursor before/after, requested/actual length, refill boundaries and object/class identity |
| Outcome | Loader result, controls, event budget, dropped/truncated counts and detach result |

Bulk reads, decompression, byte copies and primitive archive operations must keep
distinct event kinds. A wide memory copy is not automatically one semantic
field. An archive buffer refill must not reset the logical stream offset.

## Turn observations into generative rules

1. Separate field candidates from unexplained ranges. Retain conflicting access
   widths and the instructions that support each candidate. Reconcile them with
   primitive-reader semantics and static consumers.
2. Identify the actual loops that consume different input ranges per iteration.
   Keep repeated reads of a shared header/count separate from record-local reads.
   Record nesting, termination checks and the order of consumed ranges.
3. Compare handler signatures by module/RVA, independent of runtime base and
   source offset. Collapse child-loop execution into its own identity before
   comparing parent records. Variable child counts must not create a new parent
   type by themselves.
4. Recover length, presence, tag, reference-map and validation dependencies from
   native operations. Store an expression and its source locations, not the
   captured result from one file. Keep a path predicate separate from a format
   invariant until unrelated inputs and loader control flow support it.
5. Aggregate over an authored ladder that varies topology, counts, names,
   numerical scale and feature options. Add a corpus case for every newly
   discovered branch. Track cases that reached a handler separately from cases
   that merely opened.
6. Extend the shared symbolic grammar. Every repeated record comes from an input
   collection; every size comes from encoded contents; every object/reference
   index comes from the active archive map. Do not emit a captured trace.

## Keep research data out of the writer

Native trace values and source streams belong in the research workspace. They
may explain a field, but they must not become constructor defaults, recorded
programs, saved lengths, templates or output fallback data. A trace observes a
value; a writer needs its rule. Use the four field classes: authored input,
derived value, proven format constant and volatile/cache state. Unknowns remain
errors or explicit research gaps.

A native constructor assignment establishes fresh object state. It does not
establish the saved state of a completed model. A loader overwriting a value
does not by itself prove that zero is safe to emit. Recover the lifecycle and
measure a neutral value or compute the cache.

## Evaluate whether the method helped

For each attempt, record the blocking question before tracing, the smallest
capture, new rule and native evidence, cases added, implementation change, remote
codec result and clean vendor acceptance result. Also record collection and
analysis time, trace size, unique handlers and newly resolved versus still
unknown fields. Keep previous manual evidence separate from discoveries made
after adopting this method.

Success means a rule generalizes to hash-locked inputs and generated files pass
the complete CAD acceptance criteria. Faster collection, more hooks, byte
identity and a larger class map are intermediate measurements. Do not infer a
speedup or completeness claim from them.

The first application is tracked in the
[SOLIDWORKS 2026 usage ledger](../solidworks/records/Tupni2026.md).
