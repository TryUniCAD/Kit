# Explicit part driver and body name owners

Task `B04-SW2026-FCSTD-BOX` in PR #121. In the disclosed FreeCAD origin-box
trial, the generated body uses the creating feature's implicit label
`AdditiveBox`. The source Body label and source dimension identities are
currently retained in literal text and typed parameter bindings. The exact
2026 bodies below identify where direct names belong.

## Native saved body name

Both independently authored source files preserve their explicit body label,
three actual driver names and an unrelated depth edit after fresh reopen.
The corner rectangle uses `Body` and `Length`, `Width`, `Height`. The
centered rectangle uses `Centered Solid` and `Span`, `Rise`, `Thickness`.
The six native processes include two healthy controls. All four baseline and
named Config-0 partitions decode and re-emit with exact byte identity.

Both named partitions attach `SDL/TYSA_NAME` to the actual kind-12 body.
The attribute uses a kind-80 definition with type ID 8017 and a single
kind-3 field. Its value is a kind-84 character vector whose byte count follows
the name. The current partition rollback deletes the character value when
the body is removed. The four additional active nodes are the identifier,
definition, attribute and character value. The baseline uses the feature's
implicit body label.

The named `gcBody_w::setName` export is the same entry as
`gcTopEnt_w::setName` at `0x438a43b0`. The complete range
`[0x438a43b0,0x438a4482)` hashes to
`18da9acd71b2d65a5cb33ed928a837a1dd3026752fb8dabdcc9a31dadee647c3`.
Its attribute definition lookup points at the `SDL/TYSA_NAME` literal at
`0x43f69488`. It converts the input through `WideCharToMultiByte` using
thread code page 3 and writes field zero. The decoded and observed text here
is ASCII. Wider name encoding needs further qualification.

[Name ownership receipt](../measurements/2026/SdkPartNamingArchive01.json)
[Independent typed partition inspection](../../tooling/sw2026/InspectPartNamedArchive.py)

## Separate internal name setter

In `sldgcu.dll` the explicit `gcBody_w::setSWBodyName` export shares the
name-writing entry at `0x438a4490` with a face wrapper. Its complete range
`[0x438a4490,0x438a455d)` has SHA-256
`a949fdec10d0fa2a8530fd5454525e8a7a30308240fc39c8795518376645a680`.
The routine resolves or creates the named attribute on the supplied entity.
It converts the input through `WideCharToMultiByte` with code page 3 and
writes field zero. The implicit setter has separate range
`[0x438a4560,0x438a45ab)`, SHA-256
`71df35a810ae6ce3c5072d8d488e879c65d8fad60b01fafc9abba3026a6ee50a`.

The explicit attribute's actual pointer `0x44165908` is assigned through
the kernel switch from import slot `0x43f5dd38`. In
`sldgciParau.dll` that import resolves to
`gciStringAttrib_w::bodyName_ad` at `0x3312d430`. Its initializer
`0x32f9f254–0x32f9f277` constructs `SW_INTERNAL_BODY_NAME` from the
literal at `0x330b85f8` with three zero option arguments. The ordinary
constructor `0x32f9cb60` passes five owner classes
`5006, 5004, 5003, 5002, 2003` and two character fields to its
attribute-definition builder. The measured setter addresses field zero.
The two disclosed `IBody2.Name` saves carry the separate native saved body
name above. The internal setter's persistence semantics remain unqualified.

The exact bridge digests are
`77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594`
for `sldgcu.dll` and
`96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`
for `sldgciParau.dll`. REA module evidence is
`ev_153b7f59962470a7731e04d8bba49b82bbe643c0287548b68a849d3b83930e59`.

## Dimension name

The pinned `sldmodu.dll` export `Dimension_c::setParameterName` at
`0x4c821c40` resolves the actual selected dimension parameter via slot
`0xa0`. It passes that object and the supplied wide name to
`moParameter_c::setName` at `0x4c19c9b0`. The latter delegates the
string assignment to `0x4b555250`, which constructs or updates the actual
name-holder pointer at object offset `0x18`. The setter also checks a
resource-derived special name before applying a flag. Both save differentials
bind each ordinary custom name to its `moLengthParameter_c.f18`
`moNodeName_c` holder. The first two parameters are owned by the sketch
dimensions. The third belongs to the extrusion's primary end. The lengths,
unset alternate references and scalar flags retain their measured values.

The module SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The two complete setter ranges hash to
`0e415a01819436714d3a891db3df28dc48fa5e99d3f7f110122343bb99f7d1dc`
and `a2b861de02ee0d3bb4e235a5d2257ca2b507e81558ac3ad2406ecb08c5b4c48b`
respectively. [Registered dimension name API](https://help.solidworks.com/2025/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IDimension~Name.html)

## Disclosed authoring protocol

`AuthorPartDriverNames.py` uses the registered 2026 name setters on two
independently authored rectangular parts. It saves a baseline and a named
derivative, measures all three real parameter owners and the solid label,
and reopens the named output in a distinct process. An independent depth
edit checks that the named driver remains writable. Both pristine controls
and the exact frozen source hashes are mandatory.

The frozen disclosed packet hash is
`8d87b77a9cfddf4fd286c0d32626a886f27f332287e7008679641399be63bcc7`.
This is a disclosed source-only measurement. Production construction, the
generated FreeCAD body's source label and held-out name qualification remain
open.
