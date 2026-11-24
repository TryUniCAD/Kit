# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from tests.Research.Inference.Authoring.Contracts.ReadObject import ReadObject
from tests.Research.Inference.Authoring.Contracts.ReadText import ReadText
from tests.Research.Inference.Authoring.Contracts.ReadValues import ReadValues


# emitted capture jobs must retain the exact registered or legacy artifact transport contract
def VerifyCaseJob(
    Identity: str,
    Selection: dict[str, object],
    Capture: dict[str, object],
    Selector: dict[str, object],
    Records: dict[str, object],
) -> None:
    ArtifactRole = ReadText(Selector["artifact"])
    if Capture["kind"] == "capture.catalogue.solidworks.batch":
        Bound = ReadObject(Records[ReadText(ReadObject(Capture["inputs"])["cases"])])
        BoundSamples = ReadValues(Bound["samples"])
        assert Bound["schema_version"] == 1 and 1 <= len(BoundSamples) <= 3
        assert Identity in {ReadObject(Entry)["sample"] for Entry in BoundSamples}
        assert ArtifactRole in {"bundle.0", "bundle.1", "bundle.2"}
        Position = int(ArtifactRole.split(".")[1])
        Member = ReadObject(BoundSamples[Position])
        assert Member["sample"] == Identity
        assert Member["case"] == {
            FieldName: FieldValue
            for FieldName, FieldValue in Selection.items()
            if FieldName != "id"
        }
    else:
        assert Capture["kind"] == "capture.catalogue.solidworks"
        assert ArtifactRole == "bundle"
