"""
Ad-hoc Verification — NVIDIA NIM Throughput Infrastructure.
Laeuft ohne API-Key, testet Kernlogik.
Standalone-Skript (ausserhalb des Packages).
"""
import sys, os, tempfile, json, shutil, asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nim_nvidia.router import TaskType, ModelRouter
from nim_nvidia.rate_limiter import TokenBucket, PerModelLimiter, MultiModelRateLimiter
from nim_nvidia.backoff import ExponentialBackoff, RetryState
from nim_nvidia.request_queue import PriorityLevel, PrioritizedRequest, RequestQueue
from nim_nvidia.cache import ResponseCache, BatchDetector
from nim_nvidia.monitor import Monitor, estimate_cost
from nim_nvidia.client import NIMConfig

errors = 0

def check(label, condition, detail=""):
    global errors
    if condition:
        print(f"  OK  {label}")
    else:
        print(f"  FAIL {label} {detail}")
        errors += 1

print("=== 1. ROUTER ===")
router = ModelRouter()
for prompt, expected in [
    ("Analysiere Vor- und Nachteile von Microservices", TaskType.REASONING),
    ("Schreib eine Python-REST-API mit FastAPI", TaskType.CODING),
    ("Fasse dieses 50-Seiten-Dokument zusammen", TaskType.LONG_CONTEXT),
    ("Guten Morgen!", TaskType.UNKNOWN),
]:
    tt, ep = router.classify_and_resolve(prompt)
    check(f"{expected.value:15s} -> {ep.name:20s} RPM:{ep.rpm_limit}", tt == expected)

print("\n=== 2. TOKEN BUCKET ===")
bucket = TokenBucket(max_tokens=35, refill_rate=35/60)
check("initial 35 tokens", bucket.tokens == 35.0)
w1 = bucket.acquire(1.0)
check("acquire instantly", w1 == 0.0)
check("tokens consumed", abs(bucket.tokens - 34.0) < 0.01)

print("\n=== 3. BACKOFF ===")
state = RetryState(max_attempts=5, base_delay=1.0, jitter_factor=0)
delays = [round(state.next_delay(), 1) for _ in range(5)]
check("delays 1,2,4,8,16", delays == [1.0, 2.0, 4.0, 8.0, 16.0])
check("exhausted after 5", state.is_exhausted)

print("\n=== 4. CACHE ===")
cache = ResponseCache(default_ttl=300)
k = cache.make_key("m1", "hello world")
cache.set(k, {"content": "hi"}, model_name="m1")
check("cache hit", cache.get(k) is not None)
check("cache miss", cache.get("nope") is None)
check("stats", cache.stats["hits"] == 1 and cache.stats["misses"] == 1)

print("\n=== 5. MONITOR ===")
log_dir = tempfile.mkdtemp(prefix="hermes-verify-nim-")
mon = Monitor(log_dir=log_dir)
mon.record("glm-5.2", 123, 500, 200, 200)
mon.record("glm-5.2", 50, 0, 0, 429)
mon.record("deepseek-v4-pro", 30, 0, 0, 200, cache_hit=True)
s = mon.summary()
check("3 requests", s["total_requests"] == 3)
check("1 rate-limit", s["total_429s"] == 1)
check("cost > 0", s["estimated_cost_usd"] > 0)
check("log file created", len(os.listdir(log_dir)) > 0)
shutil.rmtree(log_dir, ignore_errors=True)

print("\n=== 6. COST ===")
c1 = estimate_cost("glm-5.2", 1_000_000, 1_000_000)
c2 = estimate_cost("deepseek-v4-pro", 1_000_000, 500_000)
check("GLM 1M+1M = $2.00", round(c1, 4) == 2.00)
check("DeepSeek 1M+0.5M = $1.75", round(c2, 4) == 1.75)

print("\n=== 7. BATCH ===")
bd = BatchDetector(window=5.0, min_batch_size=2)
check("first no batch", not bd.should_batch("m", "a"))
check("second triggers batch", bd.should_batch("m", "b"))
check("collects both", len(bd.get_batch("m")) == 2)

print("\n=== 8. QUEUE PRIORITY ===")
async def qtest():
    q = RequestQueue()
    bg = PrioritizedRequest(1, 1.0, "bg", "m", "bg", metadata={"l": "bg"})
    fg = PrioritizedRequest(0, 2.0, "fg", "m", "fg", metadata={"l": "fg"})
    await q._queue.put(bg)
    await q._queue.put(fg)
    r1, r2 = await q.dequeue(), await q.dequeue()
    return r1.metadata["l"], r2.metadata["l"]
a, b = asyncio.run(qtest())
check("FG before BG in queue", a == "fg" and b == "bg")

print("\n=== 9. MULTI-MODEL LIMITER ===")
ml = MultiModelRateLimiter(router.endpoints)
check("separate limiters", ml.get_limiter("glm-5.2") is not ml.get_limiter("deepseek-v4-pro"))

print("\n=== 10. CONFIG ===")
cfg = NIMConfig()
check("base_url correct", cfg.base_url == "https://integrate.api.nvidia.com/v1/")
check("default max_tokens", cfg.default_max_tokens == 4096)

print(f"\n{'='*50}")
if errors == 0:
    print("ALL 10 CHECKS PASSED")
else:
    print(f"{errors} CHECK(S) FAILED")
sys.exit(errors)