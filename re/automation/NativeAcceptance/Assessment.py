def AssessChecks(checks):
    passed = bool(checks) and all(item["status"] == "passed" for item in checks)
    gaps = sorted({item["field"] for item in checks if item["status"] == "unavailable"})
    failed = not checks or any(item["status"] not in ("passed", "unavailable") for item in checks)
    return {"status": "passed" if passed else "failed" if failed else "unverified", "full_semantics_verified": passed, "semantic_gaps": gaps}
