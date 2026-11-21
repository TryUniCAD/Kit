# Header self records are not resolved link identities

A child Header2 self record and a drawing's external file declaration are different metadata owners. Do not require their path strings to be equal merely because they refer to the same loaded source document.

In four disclosed drawing-source pairs, the actual child Header2 still records model name `Part1` and an empty self path. The drawing directory and native resolved-model observation identify the actual named child at its C: path. The native resolved child hash equals the paired exported child hash. The active child configuration and drawing selector also agree. The private normalizer initially rejected these valid resolved pairs by comparing the external declaration with Header2.

Bind the drawing declaration to the hash-bound native resolution and the actual linked child/configuration. Retain the independent Header2 values. Do not overwrite them with the directory values, infer identity from a transport basename, or merge distinct archive-map nodes by index.

Source identity proof does not remove construction limits. The current fresh `MakeSelfFile` emits one explicit output path, and `CheckPartInput` requires its basename to match the modeled part name. A source with a separate historical self identity needs that state represented or a specific refusal. Keep this constructor precondition separate from read-time resolution.
