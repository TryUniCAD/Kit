import hashlib
import re


def read_claims(root, relative):
    text = (root / relative).read_text()
    claims = []
    for section in re.split(r"(?m)(?=^#{2,4} )", text):
        heading = section.splitlines()[0] if section.splitlines() else ""
        found = re.search(r"\b[AB]\d\d[a-z]?(?:-[A-Za-z0-9]+)*\b", heading)
        if not found:
            continue
        body = section[len(heading):].strip()
        if not body or body.startswith("|"):
            continue
        state = re.search(r"\b(?:status\s*(?:is|:)?|is currently|task\s+`?[AB]\d\d[a-z]?(?:-[A-Za-z0-9]+)*`?\s+is|owns this)\s+(planned|active|blocked|checking|complete)\b", body[:1800], re.I)
        claims.append({"Id": "claim:" + found[0] + ":" + hashlib.sha256((relative + heading).encode()).hexdigest()[:8],
                       "TaskId": found[0], "Name": heading.lstrip("# "), "Status": state[1].lower() if state else "unverified",
                       "Owner": "See owning register", "Source": relative, "Excerpt": body})
    return claims
