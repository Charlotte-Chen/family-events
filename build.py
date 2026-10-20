"""執行所有 adapter，合併成 data/events.json。"""
import json, sys, traceback
from datetime import datetime, timezone, timedelta
from adapters import ADAPTERS
from adapters.common import CAT_LABEL
TZ = timezone(timedelta(hours=8))
def main():
    today = datetime.now(TZ).date()
    events, stats, prev = [], {}, {}
    try: prev = {e["id"]: e for e in json.load(open("data/events.json"))["events"]}
    except Exception: pass
    for a in ADAPTERS:
        try:
            ev = a.fetch(today); stats[a.NAME] = {"label": a.LABEL, "count": len(ev), "ok": True}
        except Exception as e:
            traceback.print_exc()
            ev = [x for x in prev.values() if x["source"] == a.NAME and x["end"] >= today.isoformat()]
            stats[a.NAME] = {"label": a.LABEL, "count": len(ev), "ok": False, "error": str(e)[:200]}
        events += ev
    seen, uniq = set(), []
    for e in sorted(events, key=lambda e: (e["start"], e["title"])):
        k = (e["title"], e["start"], e["venue"])
        if k in seen: continue
        seen.add(k); uniq.append(e)
    if not uniq: sys.exit("no events; refusing to overwrite")
    json.dump({"generatedAt": datetime.now(TZ).isoformat(timespec="minutes"), "sources": stats, "categories": CAT_LABEL,
               "events": uniq}, open("data/events.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(json.dumps(stats, ensure_ascii=False), len(uniq))
if __name__ == "__main__": main()
