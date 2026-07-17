"""
TB-5: Autonomer Watchdog-Loop.

Periodisch (via cron, alle Xh) ausgefuehrt:
  1. neue PD-Quelle scannen (TB-1)
  2. aufbereiten (TB-2)
  3. bei GUMROAD_API_KEY vorhanden: hochladen (TB-3)
Wenn kein Key: nur Corpus wachsen lassen (Entwurf), kein Echtbetrieb.

Startet den Sale-Webhook (TB-4) als Hintergrundprozess, wenn Secret da ist.
Aehnlich wa_watchdog.py (bewaehrtes Muster).
"""
import os, sys, subprocess, time, datetime, glob

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)

WAKE_LOG = os.path.join(os.path.dirname(HERE), "loop_log.txt")

def log(*a):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} " + " ".join(str(x) for x in a)
    with open(WAKE_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)

def main():
    log("=== autonomous loop tick ===")
    # 1 + 2: scan a fresh batch (Gutenberg top IDs not yet in corpus)
    import pd_scanner as sc
    existing = {os.path.basename(p) for p in glob.glob(os.path.join(sc.CORPUS, "*")) if os.path.isdir(p)}
    # kleine frische Sample-Liste (Public-Domain, EU Leben+70J)
    fresh = [
        ("25913", "Metamorphosen", "Ovid"),
        ("2701", "Moby-Dick", "Herman Melville"),
        ("174", "The Adventures of Tom Sawyer", "Mark Twain"),
        ("345", "Dracula", "Bram Stoker"),
        ("84", "Frankenstein", "Mary Shelley"),
    ]
    batch = [x for x in fresh if x[0] not in existing]
    if batch:
        res = sc.scan(batch)
        log(f"scanned {len(res)} new works")
        import pd_processor as pr
        for bid, _, _ in batch:
            if os.path.exists(os.path.join(sc.CORPUS, bid, "text.txt")):
                try:
                    pr.build_product(bid)
                    log(f"processed {bid}")
                except Exception as e:
                    log(f"process {bid} err: {e}")
    else:
        log("no fresh works, corpus stable")

    # 3: upload if key present
    try:
        import gumroad_uploader as gu
        if gu.get_key():
            for bid in existing:
                if os.path.exists(os.path.join(sc.CORPUS, bid, "product", "meta.json")):
                    ok, det = gu.publish(bid)
                    log(f"upload {bid}: {'OK' if ok else 'BLOCK'} {det}")
            # 4: poll sales (replaces webhook — no public URL needed)
            import sale_poller as sp
            n, det = sp.poll()
            log(f"sales poll: {det}")
        else:
            log("no GUMROAD_API_KEY -> Entwurf-Modus (corpus waechst, kein Upload)")
    except Exception as e:
        log(f"upload/sales phase err: {e}")

    log("loop tick done")

if __name__ == "__main__":
    main()
