# Explicit part driver and body name owners

Task `B04-SW2026-FCSTD-BOX` in PR #121. In the disclosed FreeCAD origin-box
trial, the generated body uses the creating feature's implicit label
`AdditiveBox`. The source Body label and source dimension identities are
currently retained in literal text and typed parameter bindings. The exact
2026 bodies below identify where direct names belong.

## Kernel body name

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
Observed serialized use of the second field and the full persisted body
relationship remain to be checked on independently renamed native inputs.

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
resource-derived special name before applying a flag. The ordinary custom
name proof still needs the two native-save differentials.

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
This records static ownership and a source-only experiment. Production
construction, the generated FreeCAD body's source label and held-out name
qualification remain open.
