"""執行所有 adapter，合併成 data/events.json。"""
import json, sys, os, traceback
from datetime import datetime, timezone, timedelta
from adapters import ADAPTERS
from adapters.common import CAT_LABEL
import postprocess
TZ = timezone(timedelta(hours=8))
def main():
    today = datetime.now(TZ).date(); os.makedirs("data/raw", exist_ok=True)
    events, stats, prev = [], {}, {}

    for a in ADAPTERS:
        try:
            ev = a.fetch(today)
            if not ev: raise RuntimeError("0 筆")
            json.dump(ev, open(f"data/raw/{a.NAME}.json", "w"), ensure_ascii=False)
            stats[a.NAME] = {"label": a.LABEL, "count": len(ev), "ok": True}
        except Exception as e:
            traceback.print_exc()
            try: ev = json.load(open(f"data/raw/{a.NAME}.json"))
            except Exception: ev = []
            stats[a.NAME] = {"label": a.LABEL, "count": len(ev), "ok": False, "error": str(e)[:200]}
        events += ev
    import re
    PRI = {"atpass": 0, "moc": 1, "ntpc": 2}
    seen, uniq = {}, []
    for e in sorted(events, key=lambda e: (PRI.get(e["source"], 9), e["start"], e["title"])):
        k = (re.sub(r"^\s*【[^】]*】\s*|\s+", "", e["title"]), e["start"][:7])
        if k in seen and seen[k] != e["source"]: continue
        seen.setdefault(k, e["source"]); uniq.append(e)
    if not uniq: sys.exit("no events; refusing to overwrite")
    uniq = [postprocess.expand(e, today) for e in uniq]
    uniq = [e for e in uniq if e["occurrences"] or e["longRunning"]]
    dated = {e["title"].strip() for e in uniq if e["occurrences"]}
    uniq = [e for e in uniq if e["occurrences"] or e["title"].strip() not in dated]
    try: print("geocoded new:", postprocess.geocode_all(uniq))
    except Exception: traceback.print_exc()
    json.dump({"generatedAt": datetime.now(TZ).isoformat(timespec="minutes"), "sources": stats, "categories": CAT_LABEL,
               "events": uniq}, open("data/events.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(json.dumps(stats, ensure_ascii=False), len(uniq))
if __name__ == "__main__": main()
