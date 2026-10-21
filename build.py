"""執行所有 adapter，合併成 data/events.json。"""
import json, sys, os, traceback
from datetime import datetime, timezone, timedelta
from adapters import ADAPTERS
from adapters.common import CAT_LABEL
import postprocess, cost
TZ = timezone(timedelta(hours=8))
def main():
    today = datetime.now(TZ).date(); os.makedirs("data/raw", exist_ok=True)
    events, stats, prev = [], {}, {}

    for a in ADAPTERS:
        try:
            ev = a.fetch(today)
            if not ev: raise RuntimeError("0 筆")
            try: old = json.load(open(f"data/raw/{a.NAME}.json"))
            except Exception: old = []
            if len(ev) < 0.7 * len(old):  # 來源暫時少很多筆：保留上次仍有效的活動
                ids = {x["id"] for x in ev}
                keep = [x for x in old if x["id"] not in ids and x["end"] >= today.isoformat()]
                print(f"{a.NAME}: 只抓到 {len(ev)} 筆（上次 {len(old)}），補回 {len(keep)} 筆舊資料"); ev += keep
            json.dump(ev, open(f"data/raw/{a.NAME}.json", "w"), ensure_ascii=False)
            stats[a.NAME] = {"label": a.LABEL, "count": len(ev), "ok": True}
        except Exception as e:
            traceback.print_exc()
            try: ev = json.load(open(f"data/raw/{a.NAME}.json"))
            except Exception: ev = []
            stats[a.NAME] = {"label": a.LABEL, "count": len(ev), "ok": False, "error": str(e)[:200]}
        events += ev
    import re
    PRI = {"atpass": 0, "ntsec": 0, "moc": 1, "ntpc": 2, "tsf": 3, "beclass": 5}
    seen, uniq = {}, []
    for e in sorted(events, key=lambda e: (PRI.get(e["source"], 9), e["start"], e["title"])):
        k = (re.sub(r"^\s*【[^】]*】\s*|\s+", "", e["title"]), e["start"][:7])
        if k in seen and seen[k] != e["source"]: continue
        k2 = (e["source"], e["title"], e["sessions"][0]["start"] if e.get("sessions") else e["start"])
        if k2 in seen: continue
        seen[k2] = 1
        seen.setdefault(k, e["source"]); uniq.append(e)
    if not uniq: sys.exit("no events; refusing to overwrite")
    uniq = [postprocess.tag(postprocess.expand(e, today)) for e in uniq]
    try: print("opentix price fetched:", cost.enrich_opentix(uniq))
    except Exception: traceback.print_exc()
    uniq = [cost.apply(e) for e in uniq]
    uniq = [e for e in uniq if e["occurrences"] or e["longRunning"]]
    dated = {e["title"].strip() for e in uniq if e["occurrences"]}
    uniq = [e for e in uniq if e["occurrences"] or e["title"].strip() not in dated]
    try: print("geocoded new:", postprocess.geocode_all(uniq))
    except Exception: traceback.print_exc()
    json.dump({"generatedAt": datetime.now(TZ).isoformat(timespec="minutes"), "sources": stats, "categories": CAT_LABEL, "ageBuckets": [[k, l] for k, l, _, _ in postprocess.AGE_BUCKETS], "topics": list(postprocess.TOPICS),
               "events": uniq}, open("data/events.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(json.dumps(stats, ensure_ascii=False), len(uniq))
if __name__ == "__main__": main()
