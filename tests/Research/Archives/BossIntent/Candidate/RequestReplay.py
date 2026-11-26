# the parent verifies the actual constructor result and audited inputs after process exit
KRequestReplay = """
# a changed external request must fail against the separately retained digest
KPayload = KRequestPath.read_bytes()

# the test needs the production research constructor result without writing another model file
KReport = GenerateRequest(KPayload, sys.argv[3], context, candidate=None)
print(WriteJson({"result": KReport, "model_reads": sorted(KObservedReads)}))
"""
