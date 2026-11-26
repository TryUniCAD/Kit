# Preserve P03 keyword dimension order

The constrained Boss research can carry the prepared P03 source's dimension order into the generated keyword index. The opt-in call checks the two saved distance relation IDs, driving parameter IDs and ordered endpoints against the typed target sketch. The package encoder keeps generating each named dimension from the authored length. [P03 candidate preparation](ConstrainedBossCandidate.md)

## Replay

Prepare a canonical request and retain its SHA-256 using the existing P03 procedure. Run a fresh Python 3.14 process with the persisted request and the same explicit `PortableBossContext` used for the default replay. The recorded request SHA-256 is `d460d8352b7e34526a5e95d451d5671454d8b30d8ef96e5adf90111d67812a49`; the retained caller context SHA-256 is `796f3924afbff0adef17e4e215f67a0ddf2a17d1f83f09418f9f969f90ae716c`.

```python
report = generate_request(
    request_bytes,
    retained_request_sha256,
    context,
    candidate=unused_candidate_path,
    preserve_keyword_order=True,
)
```

With the option omitted, the default package still emits width before height. The opt-in does not read the native source or copy its XML. It routes the checked order through the existing keyword encoder before packaging. The independent package XML verifier checks that order.

## Offline evidence

The default process reproduced candidate SHA-256 `a0e524cc73b844042c7da6bf86b3a12120fb4f73aaf34de7f0d6cc481ebda15f`. Two source-order processes reproduced `29b581feaf693b2a5e38e2f8bac70d2f3ab2b7f3f4f56be104e64701e0c0a62a`. Only the clear `swXmlContents/KeyWords` stream differed. The other 31 streams, including both feature streams and the PMI index, agreed byte for byte. The generated binary records retained width 40 mm then height 20 mm, their IDs, ordered point operands and shared corners.

The unmodified pinned reader at `c0a401a607759fb0c2589647c2a22af65ebb7ce1` projected height then width and verified all seven saved relations and four inferred corner joins on the opt-in archive. The default archive refused the same ordered-relation check. Four fresh rehashed requests refused before output for a duplicated distance row, foreign parameter ID, swapped endpoints or contradictory row order. The exact default archive also refused the package XML check when verified against the source-order state. [Exact verification report](../../../../re/solidworks/measurements/2026/P03KeywordDimensionOrder.json)

The maintained P03 process case pins both default replays to the default SHA-256, verifies the published opt-in archive against the source-order SHA-256, and confirms that a rehashed request with reversed distance rows exits without publishing. The focused case passed in 78.20 seconds on Windows with Python 3.14.6. The merge planner assigned that case to one shard in a targeted collection. [P03 candidate process case](../../../../tests/Research/Archives/BossIntent/Candidate/CandidateTests.py)

The pinned public model-only read still projects Join for both generated archives. The authored target remains Create. The default strict read still refuses the generated candidates for lack of a readable Parasolid payload. Complete typed linking still refuses `moSimpleSurfIdRep_c` schema 1. Native lifecycle and whole-source fidelity remain unverified. [Keyword order gotcha](../../../Gotchas/Research/Readers/SolidworksKeywordOrderCanDifferFromBinaryDimensions.md)
