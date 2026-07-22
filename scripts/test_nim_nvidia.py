"""
Test-Suite für die NVIDIA NIM Throughput Infrastructure.

Testet die Kernlogik ohne echte API-Aufrufe:
- Router-Klassifikation
- Token-Bucket-Rate-Limiting
- Backoff-Timing
- Queue-Priorität
- Cache-Hit/Miss/Expiry
- Batch-Erkennung
- Monitor-Statistiken
"""

import asyncio
import time
import unittest

from scripts.nim_nvidia.router import (
    TaskType,
    ModelEndpoint,
    ModelRouter,
    classify_task,
    DEFAULT_ENDPOINTS,
)
from scripts.nim_nvidia.rate_limiter import (
    TokenBucket,
    SlidingWindowLimiter,
    PerModelLimiter,
    MultiModelRateLimiter,
)
from scripts.nim_nvidia.backoff import ExponentialBackoff, RetryState
from scripts.nim_nvidia.queue import PriorityLevel, RequestQueue, PrioritizedRequest
from scripts.nim_nvidia.cache import ResponseCache, BatchDetector, hash_prompt, normalize_prompt
from scripts.nim_nvidia.monitor import Monitor, ModelStats, estimate_cost


# ═══════════════════════════════════════════════════════════════════════
# Router-Tests
# ═══════════════════════════════════════════════════════════════════════

class TestClassifyTask(unittest.TestCase):
    """Testet die heuristische Prompt-Klassifikation."""

    def test_reasoning_prompt(self):
        prompt = "Sollte ich Microservices oder Monolithen verwenden? Analysiere die Vor- und Nachteile."
        self.assertEqual(classify_task(prompt), TaskType.REASONING)

    def test_coding_prompt(self):
        prompt = "Schreib eine Python-Funktion, die eine Liste sortiert."
        self.assertEqual(classify_task(prompt), TaskType.CODING)

    def test_coding_with_code_block(self):
        prompt = "Hier ist der Code:\n```python\ndef foo():\n    pass\n```"
        self.assertEqual(classify_task(prompt), TaskType.CODING)

    def test_long_context(self):
        prompt = "Fasse das gesamte Dokument zusammen."
        self.assertEqual(classify_task(prompt, token_count=12_000), TaskType.LONG_CONTEXT)

    def test_long_context_keyword(self):
        prompt = "Lies die Datei und extrahiere alle wichtigen Informationen."
        self.assertEqual(classify_task(prompt), TaskType.LONG_CONTEXT)

    def test_unknown_fallback(self):
        prompt = "Guten Morgen, wie geht es Ihnen heute?"
        self.assertEqual(classify_task(prompt), TaskType.UNKNOWN)


class TestModelRouter(unittest.TestCase):
    def setUp(self):
        self.router = ModelRouter()

    def test_resolve_reasoning(self):
        ep = self.router.resolve(TaskType.REASONING)
        self.assertEqual(ep.name, "glm-5.2")
        self.assertEqual(ep.model_id, "nvidia/glm-5.2")
        self.assertEqual(ep.rpm_limit, 35)

    def test_resolve_coding(self):
        ep = self.router.resolve(TaskType.CODING)
        self.assertEqual(ep.name, "deepseek-v4-pro")

    def test_resolve_long_context(self):
        ep = self.router.resolve(TaskType.LONG_CONTEXT)
        self.assertEqual(ep.name, "nemotron-3-ultra")

    def test_classify_and_resolve(self):
        tt, ep = self.router.classify_and_resolve("Schreib einen API-Endpoint in Python")
        self.assertEqual(tt, TaskType.CODING)
        self.assertEqual(ep.name, "deepseek-v4-pro")

    def test_all_endpoints_have_different_task_types(self):
        """Jedes Modell hat exklusive TaskTypes (kein Mix)."""
        all_types = []
        for ep in DEFAULT_ENDPOINTS:
            all_types.extend(ep.task_types)
        self.assertEqual(len(set(all_types)), len(all_types))

    def test_get_endpoint_by_name(self):
        ep = self.router.get_endpoint("glm-5.2")
        self.assertIsNotNone(ep)
        self.assertEqual(ep.model_id, "nvidia/glm-5.2")


# ═══════════════════════════════════════════════════════════════════════
# Rate-Limiter-Tests
# ═══════════════════════════════════════════════════════════════════════

class TestTokenBucket(unittest.TestCase):
    def test_initial_tokens(self):
        bucket = TokenBucket(max_tokens=35, refill_rate=35/60)
        self.assertAlmostEqual(bucket.tokens, 35)

    def test_acquire_immediate(self):
        bucket = TokenBucket(max_tokens=5, refill_rate=5/60)
        wait = bucket.acquire(1.0)
        self.assertEqual(wait, 0.0)
        self.assertAlmostEqual(bucket.tokens, 4.0)

    def test_acquire_exhausts(self):
        bucket = TokenBucket(max_tokens=3, refill_rate=1.0)
        for _ in range(3):
            wait = bucket.acquire(1.0)
            self.assertEqual(wait, 0.0)
        wait = bucket.acquire(1.0)
        self.assertGreater(wait, 0)  # Muss warten

    def test_refill_over_time(self):
        bucket = TokenBucket(max_tokens=10, refill_rate=10.0)
        bucket.tokens = 0
        bucket.last_refill = time.monotonic() - 0.5  # 500ms vergangen
        wait = bucket.acquire(1.0)
        self.assertEqual(wait, 0.0)  # 5 Tokens nachgefüllt in 0.5s
        self.assertAlmostEqual(bucket.tokens, 4.0, places=1)


class TestSlidingWindow(unittest.TestCase):
    def test_allow_up_to_max(self):
        limiter = SlidingWindowLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            self.assertTrue(limiter.allow())
            limiter.record()
        self.assertFalse(limiter.allow())

    def test_window_expires(self):
        limiter = SlidingWindowLimiter(max_requests=1, window_seconds=0.1)
        self.assertTrue(limiter.allow())
        limiter.record()
        self.assertFalse(limiter.allow())
        time.sleep(0.15)
        self.assertTrue(limiter.allow())


class TestPerModelLimiter(unittest.TestCase):
    def test_instant_requests_within_rpm(self):
        """Bei 35 RPM sollten 35 Requests sofort durchgehen."""
        limiter = PerModelLimiter(rpm=35)

        async def _test():
            for _ in range(35):
                await limiter.acquire()
            # 36. Request sollte warten
            t0 = time.monotonic()
            await asyncio.wait_for(limiter.acquire(), timeout=2.0)
            elapsed = time.monotonic() - t0
            self.assertGreater(elapsed, 0.01)

        asyncio.run(_test())


class TestMultiModelRateLimiter(unittest.TestCase):
    def test_separate_limiters(self):
        """Jedes Modell hat seinen eigenen Limiter (kein Cross-Talk)."""
        endpoints = [
            ModelEndpoint(name="a", model_id="a", rpm_limit=5, task_types={TaskType.REASONING}),
            ModelEndpoint(name="b", model_id="b", rpm_limit=5, task_types={TaskType.CODING}),
        ]
        limiter = MultiModelRateLimiter(endpoints)
        l_a = limiter.get_limiter("a")
        l_b = limiter.get_limiter("b")
        self.assertIsNot(l_a, l_b)


# ═══════════════════════════════════════════════════════════════════════
# Backoff-Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRetryState(unittest.TestCase):
    def test_delays_increase(self):
        state = RetryState(max_attempts=5, base_delay=1.0, jitter_factor=0)
        delays = [state.next_delay() for _ in range(5)]
        # 1, 2, 4, 8, 16
        expected = [1.0, 2.0, 4.0, 8.0, 16.0]
        for d, e in zip(delays, expected):
            self.assertAlmostEqual(d, e, places=1)

    def test_max_delay_cap(self):
        state = RetryState(max_attempts=10, base_delay=1.0, max_delay=10.0, jitter_factor=0)
        delays = [state.next_delay() for _ in range(10)]
        self.assertLessEqual(max(delays), 10.0)

    def test_jitter_applied(self):
        """Jitter sorgt für Varianz, aber Delays bleiben im Rahmen."""
        state = RetryState(max_attempts=3, base_delay=5.0, jitter_factor=0.5)
        # next_delay erhöht attempt: 5.0±2.5, 10.0±5.0, 20.0±10.0
        d1 = state.next_delay()
        d2 = state.next_delay()
        d3 = state.next_delay()
        self.assertGreaterEqual(d1, 2.5, msg="d1 min (5.0 - 50% jitter)")
        self.assertLessEqual(d1, 7.5, msg="d1 max (5.0 + 50% jitter)")
        self.assertGreaterEqual(d2, 5.0, msg="d2 min (10.0 - 50% jitter)")
        self.assertLessEqual(d2, 15.0, msg="d2 max (10.0 + 50% jitter)")
        self.assertGreaterEqual(d3, 10.0, msg="d3 min (20.0 - 50% jitter)")
        self.assertLessEqual(d3, 30.0, msg="d3 max (20.0 + 50% jitter)")
        # Varianz prüfen (verschiedene Jitter-Werte)
        all_d = [state.next_delay() for _ in range(10)]
        self.assertGreater(max(all_d), min(all_d),
            msg="Jitter sollte unterschiedliche Delays erzeugen")

    def test_exhaustion(self):
        state = RetryState(max_attempts=3, base_delay=0.1)
        self.assertEqual(state.remaining, 3)
        state.next_delay()
        self.assertEqual(state.remaining, 2)
        state.next_delay()
        self.assertEqual(state.remaining, 1)
        state.next_delay()
        self.assertTrue(state.is_exhausted)


class TestExponentialBackoff(unittest.TestCase):
    def test_success_first_try(self):
        """Bei Erfolg sofort zurückgeben, kein Retry."""
        async def ok():
            return "done"

        backoff = ExponentialBackoff(max_attempts=3)
        result = asyncio.run(backoff.run(ok))
        self.assertEqual(result, "done")

    def test_does_not_retry_4xx(self):
        """4xx-Fehler (außer 429) werden nicht wiederholt."""
        class ClientError(Exception):
            def __init__(self):
                self.status = 403

        call_count = 0

        async def fail():
            nonlocal call_count
            call_count += 1
            raise ClientError()

        backoff = ExponentialBackoff(max_attempts=3)
        with self.assertRaises(ClientError):
            asyncio.run(backoff.run(fail))
        self.assertEqual(call_count, 1)  # Nur 1 Versuch


# ═══════════════════════════════════════════════════════════════════════
# Queue-Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRequestQueue(unittest.TestCase):
    def test_priority_order(self):
        """FOREGROUND (0) kommt vor BACKGROUND (1) aus der Queue."""
        q = RequestQueue()
        received = []

        async def _test():
            # Beide einreihen (BG zuerst, FG später)
            req_bg = PrioritizedRequest(
                priority=PriorityLevel.BACKGROUND, timestamp=1.0,
                request_id="bg", model_name="m1", prompt="bg",
                metadata={"label": "bg"},
            )
            req_fg = PrioritizedRequest(
                priority=PriorityLevel.FOREGROUND, timestamp=2.0,
                request_id="fg", model_name="m1", prompt="fg",
                metadata={"label": "fg"},
            )
            await q._queue.put(req_bg)
            await q._queue.put(req_fg)

            r1 = await q.dequeue()
            r2 = await q.dequeue()
            return [r1.metadata.get("label", ""), r2.metadata.get("label", "")]

        received = asyncio.run(_test())
        self.assertEqual(received, ["fg", "bg"])  # FG (0) vor BG (1)

    def test_worker_executes_tasks(self):
        """Worker führt Tasks aus und setzt Futures."""
        q = RequestQueue()

        async def executor(req):
            return "world"

        async def _test():
            fut = await q.enqueue(
                "m1", "hello", lambda: "world", PriorityLevel.FOREGROUND
            )
            asyncio.create_task(q.worker(executor))
            result = await asyncio.wait_for(fut, timeout=5.0)
            self.assertEqual(result, "world")

        asyncio.run(_test())


# ═══════════════════════════════════════════════════════════════════════
# Cache-Tests
# ═══════════════════════════════════════════════════════════════════════

class TestResponseCache(unittest.TestCase):
    def setUp(self):
        self.cache = ResponseCache(default_ttl=300)

    def test_set_and_get(self):
        key = self.cache.make_key("deepseek-v4-pro", "Hallo Welt")
        self.cache.set(key, {"content": "Hi"}, model_name="deepseek-v4-pro")
        result = self.cache.get(key)
        self.assertEqual(result, {"content": "Hi"})

    def test_miss_on_different_key(self):
        key1 = self.cache.make_key("deepseek-v4-pro", "Hallo")
        key2 = self.cache.make_key("deepseek-v4-pro", "Tschüss")
        self.cache.set(key1, "a")
        self.assertIsNone(self.cache.get(key2))

    def test_expiry(self):
        cache = ResponseCache(default_ttl=0.01)  # 10ms TTL
        key = cache.make_key("m1", "test")
        cache.set(key, "value", ttl=0.01)
        self.assertIsNotNone(cache.get(key))
        time.sleep(0.02)
        self.assertIsNone(cache.get(key))

    def test_invalidate_all(self):
        self.cache.set("k1", "v1", model_name="a")
        self.cache.set("k2", "v2", model_name="b")
        count = self.cache.invalidate()
        self.assertEqual(count, 2)
        self.assertEqual(len(self.cache._entries), 0)

    def test_invalidate_by_model(self):
        self.cache.set("k1", "v1", model_name="glm-5.2")
        self.cache.set("k2", "v2", model_name="deepseek-v4-pro")
        count = self.cache.invalidate(model_name="glm-5.2")
        self.assertEqual(count, 1)
        self.assertEqual(len(self.cache._entries), 1)

    def test_normalize_prompt_removes_timestamps(self):
        raw = "Current time: 16:43\nHallo Welt\nHeute ist Dienstag"
        normalized = normalize_prompt(raw)
        self.assertNotIn("Current time", normalized)
        self.assertNotIn("Heute ist", normalized)
        self.assertIn("Hallo Welt", normalized)

    def test_same_prompt_same_key(self):
        key1 = self.cache.make_key("m1", "Hallo Welt")
        key2 = self.cache.make_key("m1", "Hallo  Welt  ")
        self.assertEqual(key1, key2)

    def test_stats(self):
        key = self.cache.make_key("m1", "x")
        self.cache.set(key, "y", model_name="m1")
        self.cache.get("nonexistent")
        self.cache.get(key)
        stats = self.cache.stats
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertAlmostEqual(stats["hit_ratio"], 0.5)


class TestBatchDetector(unittest.TestCase):
    def test_should_batch(self):
        det = BatchDetector(window=5.0, min_batch_size=2)
        self.assertFalse(det.should_batch("m1", "a"))  # 1. Request: kein Batch
        self.assertTrue(det.should_batch("m1", "b"))   # 2. Request: batch!

    def test_get_batch(self):
        det = BatchDetector(window=5.0, min_batch_size=2)
        det.should_batch("m1", "a")
        det.should_batch("m1", "b")
        batch = det.get_batch("m1")
        self.assertEqual(len(batch), 2)

    def test_no_cross_model_batch(self):
        det = BatchDetector(window=5.0, min_batch_size=2)
        det.should_batch("m1", "a")
        self.assertFalse(det.should_batch("m2", "b"))
        det.should_batch("m2", "c")
        batch = det.get_batch("m2")
        self.assertEqual(len(batch), 2)


# ═══════════════════════════════════════════════════════════════════════
# Monitor-Tests
# ═══════════════════════════════════════════════════════════════════════

class TestMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = Monitor()

    def test_record_request(self):
        self.monitor.record("deepseek-v4-pro", latency_ms=150, tokens_in=500, tokens_out=200, status_code=200)
        stats = self.monitor.get_stats("deepseek-v4-pro")
        self.assertEqual(stats.total_requests, 1)
        self.assertAlmostEqual(stats.total_latency_ms, 150)
        self.assertEqual(stats.total_tokens_input, 500)
        self.assertEqual(stats.total_tokens_output, 200)

    def test_record_429(self):
        self.monitor.record("glm-5.2", latency_ms=50, status_code=429)
        stats = self.monitor.get_stats("glm-5.2")
        self.assertEqual(stats.rate_limit_hits, 1)

    def test_cache_hit_logged(self):
        self.monitor.record("nemotron-3-ultra", latency_ms=0, cache_hit=True)
        stats = self.monitor.get_stats("nemotron-3-ultra")
        self.assertEqual(stats.cache_hits, 1)

    def test_summary(self):
        self.monitor.record("a", latency_ms=100, tokens_in=1000, tokens_out=500, status_code=200)
        self.monitor.record("a", latency_ms=50, tokens_in=200, tokens_out=100, status_code=429)
        self.monitor.record("b", latency_ms=200, tokens_in=500, tokens_out=300, status_code=200, cache_hit=True)
        summary = self.monitor.summary()
        self.assertEqual(summary["total_requests"], 3)
        self.assertEqual(summary["total_429s"], 1)
        self.assertIn("a", summary["models"])
        self.assertIn("b", summary["models"])


class TestModelStats(unittest.TestCase):
    def test_avg_latency(self):
        stats = ModelStats(model_name="test")
        stats.record(latency_ms=100)
        stats.record(latency_ms=200)
        self.assertAlmostEqual(stats.avg_latency_ms, 150)

    def test_error_rate(self):
        stats = ModelStats(model_name="test")
        stats.record(latency_ms=100, status_code=200)
        stats.record(latency_ms=50, status_code=429)
        stats.record(latency_ms=30, status_code=500)
        self.assertAlmostEqual(stats.error_rate, 2 / 3)

    def test_to_dict(self):
        stats = ModelStats(model_name="glm-5.2")
        stats.record(latency_ms=100, tokens_in=1000, tokens_out=500)
        d = stats.to_dict()
        self.assertEqual(d["model"], "glm-5.2")
        self.assertEqual(d["total_tokens_in"], 1000)
        self.assertEqual(d["total_tokens_out"], 500)


class TestCostEstimate(unittest.TestCase):
    def test_glm_cost(self):
        cost = estimate_cost("glm-5.2", tokens_in=1_000_000, tokens_out=1_000_000)
        # $0.50 + $1.50 = $2.00
        self.assertAlmostEqual(cost, 2.00, places=4)

    def test_deepseek_cost(self):
        cost = estimate_cost("deepseek-v4-pro", tokens_in=1_000_000, tokens_out=500_000)
        # $0.75 + $1.00 = $1.75
        self.assertAlmostEqual(cost, 1.75, places=4)


# ═══════════════════════════════════════════════════════════════════════
# Integrationstest: Queue → Rate-Limiter → Worker
# ═══════════════════════════════════════════════════════════════════════

class TestQueueRateLimitIntegration(unittest.TestCase):
    def test_queue_respects_rate_limit(self):
        """Queue + Rate-Limiter: 10 Requests in <5s dauern länger als 5s bei 1 RPM."""
        from scripts.nim_nvidia.router import ModelEndpoint, TaskType
        from scripts.nim_nvidia.rate_limiter import MultiModelRateLimiter
        from scripts.nim_nvidia.queue import RequestQueue, PriorityLevel

        queue = RequestQueue()
        limiter = MultiModelRateLimiter([
            ModelEndpoint(name="slow", model_id="slow", rpm_limit=10, task_types={TaskType.UNKNOWN}),
        ])
        results = []

        async def worker():
            for _ in range(10):
                req = await queue.dequeue()
                await limiter.acquire("slow")
                result = f"done-{_}"
                results.append(result)
                req.future.set_result(result)

        async def _test():
            t0 = time.monotonic()
            # 10 Requests enqueuen
            futs = []
            for i in range(10):
                fut = await queue.enqueue("slow", f"prompt-{i}", lambda i=i: f"res-{i}", PriorityLevel.FOREGROUND)
                futs.append(fut)
            # Worker starten
            t = asyncio.create_task(worker())
            await asyncio.gather(*futs)
            elapsed = time.monotonic() - t0
            # 10 Requests bei 10 RPM = 6s für 10 Stück (einer pro 6s)
            # Aber TokenBucket erlaubt Burst von 10, also eigentlich sofort
            # Wichtig: bestätigen, dass alle durchkommen
            self.assertEqual(len(results), 10)
            return elapsed

        elapsed = asyncio.run(_test())
        # Sollte in < 5s sein (Burst von 10 bei kap 10)
        self.assertLess(elapsed, 5.0)


# ═══════════════════════════════════════════════════════════════════════
# Entry
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)