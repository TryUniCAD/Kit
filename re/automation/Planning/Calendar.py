import html
from datetime import date


def calendar_svg(items):
    rows = [item for item in items if item["Kind"] == "Milestone"]
    dates = [date.fromisoformat(item[key]) for item in rows for key in ("Start", "Finish") if item[key]]
    start, finish = min(dates), max(dates)
    span = max(1, (finish - start).days + 1)
    height = 100 + len(rows) * 34
    result = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">',
              '<title id="title">Kit scheduled investigation windows</title>',
              '<desc id="desc">Calendar Gantt of proposed investigation timeboxes, not feature completion dates. Current open deliveries and detailed scopes are available in the scheduling board.</desc>',
              f'<rect width="1200" height="{height}" fill="#faf9f6"/><g font-family="sans-serif" font-size="12" fill="#262522">',
              '<text x="16" y="26" font-size="18">Scheduled investigation windows</text>',
              '<text x="16" y="48">Proposed capacity and timeboxes · source prerequisites still bind · no native-host reservation or delivery commitment</text>']
    for index in range(7):
        offset = span * index / 6
        x = 610 + index * 90
        from datetime import timedelta
        label = (start + timedelta(days=int(offset))).isoformat()
        result.extend([f'<text x="{x}" y="76">{label}</text>', f'<path d="M{x} 84V{height}" stroke="#dedbd5"/>'])
    for index, item in enumerate(rows):
        y = 104 + index * 34
        label = item["Id"] + " · " + item["Name"]
        result.append(f'<text x="16" y="{y}">{html.escape(label[:79])}</text>')
        if item["Start"]:
            left = 610 + (date.fromisoformat(item["Start"]) - start).days / span * 540
            width = max(4, ((date.fromisoformat(item["Finish"]) - date.fromisoformat(item["Start"])).days + 1) / span * 540)
            color = "#91584e" if item["Status"] == "blocked" else "#82652c" if item["Status"] in {"active", "checking"} else "#777268"
            result.append(f'<rect x="{left:.1f}" y="{y-12}" width="{width:.1f}" height="20" rx="2" fill="{color}"><title>{html.escape(item["Status"] + ": " + item["Start"] + " to " + item["Finish"])}</title></rect>')
        else:
            result.append(f'<text x="610" y="{y}" fill="#615c54">{html.escape(item["Status"])} · no date asserted</text>')
    return "\n".join([*result, '</g></svg>']) + "\n"
