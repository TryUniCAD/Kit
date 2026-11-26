# the parent verifies the actual constructor result and audited inputs after process exit
KRequestReplay = """
from hashlib import sha256 as HashBytes
from json import dumps as WriteJson

from convert.adapters.solidworks.Container.Container import SldprtArchive
from P03CandidateRequest import generate_request as GenerateRequest
from VerifyPartPreviews import read_png as ReadPng


# a changed external request must fail against the separately retained digest
KPayload = KRequestPath.read_bytes()

# publication and order selection must use the same constructor as in-memory replay
KReport = GenerateRequest(
    KPayload,
    sys.argv[3],
    context,
    candidate=KCandidatePath,
    preserve_keyword_order=sys.argv[5] == "source",
)
assert KObservedReads <= {str(AllowedPath) for AllowedPath in KAllowed}, sorted(KObservedReads)
# only a published output can supply a decoded preview verification
KPreviewPixels = None
if KCandidatePath is not None:
    KOutputReadEnabled = True
    # the existing archive reader must reopen the published bytes after the constructor returns
    KPublished = SldprtArchive.OpenAction(KCandidatePath)
    KOutputReadEnabled = False
    # pixels and resolution remain comparable when a different deflater encodes them
    KWidth, KHeight, KResolution, KPixels = ReadPng(KPublished.Require("PreviewPNG"))
    KPreviewPixels = [KWidth, KHeight, KResolution, HashBytes(KPixels).hexdigest()]
print(WriteJson({
    "result": KReport,
    "model_reads": sorted(KObservedReads),
    "preview_pixels": KPreviewPixels,
}))
"""
