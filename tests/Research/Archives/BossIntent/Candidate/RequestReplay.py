# the parent verifies the actual constructor result and audited inputs after process exit
KRequestReplay = """
from json import dumps as WriteJson
from P03CandidateRequest import generate_request as GenerateRequest


# a changed external request must fail against the separately retained digest
KPayload = KRequestPath.read_bytes()

# the test needs the production research constructor result without writing another model file
KReport = GenerateRequest(KPayload, sys.argv[3], context, candidate=None)
assert KObservedReads <= {str(AllowedPath) for AllowedPath in KAllowed}, sorted(KObservedReads)
print(WriteJson({"result": KReport, "model_reads": sorted(KObservedReads)}))
"""
