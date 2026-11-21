# Lazy codecs cross the construction boundary

## Expectation

Importing a serializer also imports every encoding implementation it will use.

## Actual behavior

The strict remote model-construction check reached `Store.string`, then Python
loaded `encodings/utf_16_le.py` on the first Unicode encode. The construction
audit correctly rejected that file access after `BeginBuild`.
The failure occurred at `236ccd510` in
[run 43680426687](https://github.com/TryUniCAD/Kit/actions/runs/43680426687).

## Workaround

Resolve the serializer's fixed codec names with `codecs.lookup` during the
recorded import phase. Then close that phase and keep all file opens, directory
enumeration and process launches forbidden throughout model construction and
serialization. Do not permit late code-file reads merely to make the audit pass.

This prepares executable dependencies; it does not construct or import native
document data. The fresh-construction evidence remains pending until the
repaired remote process check passes.
