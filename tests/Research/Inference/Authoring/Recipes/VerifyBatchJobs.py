# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from tests.Research.Inference.Authoring.Recipes.VerifyCaseJob import VerifyCaseJob
from tests.Research.Inference.Authoring.Contracts.ReadObject import ReadObject
from tests.Research.Inference.Authoring.Contracts.ReadText import ReadText
from tests.Research.Inference.Authoring.Contracts.ReadValues import ReadValues


# emitted batch jobs must isolate accepted artifact roles while legacy samples retain their original worker kind
def VerifyBatchJobs(Report: dict[str, object], PlanValue: dict[str, object]) -> None:
    JobsById = {
        ReadText(Entry["id"]): Entry
        for Value in ReadValues(Report["definitions"])
        for Entry in [ReadObject(Value)]
    }
    Records = {
        ReadText(Entry["name"]): Entry["record"]
        for Value in ReadValues(Report["bindings"])
        for Entry in [ReadObject(Value)]
    }
    SeenSamples: set[str] = set()
    SeenRoles: set[tuple[str, str]] = set()
    Samples = ReadObject(PlanValue["samples"])
    BatchLimit = PlanValue.get("solidworks_batch_size", 3)
    assert isinstance(BatchLimit, int)
    for Value in ReadValues(Report["submissions"]):
        Submission = ReadObject(Value)
        SampleIds = ReadValues(Submission["samples"])
        CaptureIds = ReadValues(Submission["capture"])
        assert len(SampleIds) == len(CaptureIds) == 1
        Identity = ReadText(SampleIds[0])
        assert Identity not in SeenSamples
        SeenSamples.add(Identity)
        Selection = ReadObject(ReadObject(Samples[Identity])["case"])
        Capture = JobsById[ReadText(CaptureIds[0])]
        Decoder = JobsById[ReadText(Submission["decode"])]
        assert Decoder["depends_on"] == [Capture["id"]]
        Selector = ReadObject(ReadObject(Decoder["inputs"])["bundle"])
        assert Selector["dependency"] == Capture["id"]
        ArtifactRole = ReadText(Selector["artifact"])
        CaptureId = ReadText(Capture["id"])
        assert (CaptureId, ArtifactRole) not in SeenRoles
        SeenRoles.add((CaptureId, ArtifactRole))
        VerifyCaseJob(
            Identity,
            Selection,
            Capture,
            Selector,
            Records,
            PlanValue.get("solidworks_batch_version") == 1,
            BatchLimit,
        )
    assert SeenSamples == set(Samples)
