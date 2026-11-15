# SOLIDWORKS type-library inventory

The [metadata inspector](../../../../re/tooling/sw2026/InspectTypeLib.py) accepts case-sensitive glob patterns for declaring types and member names.
This supports inventories of related feature-definition interfaces and enumeration constants from the installed libraries.
It reads type-library metadata without launching, attaching to, or creating a CAD application object.

The positional command remains:

```text
python re/tooling/sw2026/InspectTypeLib.py <absolute-library-path> <interface-pattern> <member-pattern>
```

For this oracle, pass the guest Python command from macOS through `prlctl exec --current-user "Windows 11"` after staging the committed inspector at a guest-accessible absolute path.
Quote patterns so the invoking shell passes them unchanged.
For example, these selections request revolve declarations and constraint constants respectively:

```text
python re/tooling/sw2026/InspectTypeLib.py <absolute-installed-sldworks-tlb-path> "*Revolve*" "*"
python re/tooling/sw2026/InspectTypeLib.py <absolute-installed-swconst-type-library-path> "swConstraintType_e" "*"
```

Patterns use Python's `fnmatchcase`, including `*`, `?`, and bracket expressions.
An exact selection such as `IFeature GetErrorCode2` continues to select that declaration.
Only members declared by matching type-information records are returned; the inspector does not recursively flatten inherited interfaces or referenced libraries.

The JSON report retains the existing `path`, `sha256`, `library`, `interface`, `method`, `methods`, and `scope` fields.
Each method retains its `names`, `member_id`, `invoke_kind`, `arguments`, and `return_type` fields.
It additionally identifies its declaring type by name, GUID, numeric type kind, and library type index.
The `types` array records matching declarations, including declarations without matching members.
The `interface` and `method` fields contain the supplied selectors, including patterns for enum queries.

The new `constants` array records matching enumeration names and integer values from `GetVarDesc`.
Each entry includes its member ID, variable kind and flags, declared type descriptor, and declaring type identity.
Methods still come from `GetFuncDesc`; argument and return descriptors retain their existing representation.
The pywin32 [descriptor definitions](https://github.com/mhammond/pywin32/blob/main/com/win32com/src/include/PyComTypeObjects.h) expose the required variable fields.
Its [type-library generator](https://github.com/mhammond/pywin32/blob/main/com/win32com/client/genpy.py) uses these descriptors to enumerate constants.
The inspector contains independently authored traversal and reporting code.

The report includes the selected library's absolute resolved path and SHA-256, plus its actual name, GUID, locale, system kind, version, and flags.
It also records the inspector path, inspector SHA-256, and Python version.
The source file is hashed before and after inspection; a changed hash aborts reporting.
No fixed SOLIDWORKS library version, enum value, or method signature is substituted for metadata.
The report is independently generated JSON; no proprietary library or generated SDK wrapper is copied.

A relative path, absent type selection, or selection without methods or constants fails explicitly.
A matching enumeration entry with a nonconstant descriptor or a noninteger value also fails explicitly.
Unsupported values are not coerced or replaced.

Python AST parsing passed, and Black `26.5.1` formatted the private script.
These checks did not import or execute the inspector.
The wildcard and enum inventory paths have not yet been exercised against the installed Windows libraries.
Fresh metadata capture remains pending and must record the actual library and tool identities.
The earlier [exact-method evidence](../../../../re/solidworks/v2026/evidence/CurveAuthoringTypeLibrary.json) does not validate these new paths.
Metadata describes API declarations; it does not establish serialized field ownership, writer correctness, geometry, or native file acceptance.
The [SOLIDWORKS adapter](../../../Reference/Adapters/Solidworks.md) remains read-only.
