"""
Live-Test: NVIDIA NIM Multi-Model via NIMClient.
Testet alle drei Modelle mit je einem echten API-Call.
"""
import sys, os, asyncio, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# API-Key wurde in der Shell als NVIDIA_API_KEY gesetzt
# (nicht in Code committed)
key = os.environ.get("NVIDIA_API_KEY", "")
if not key:
    print("FEHLER: NVIDIA_API_KEY nicht gesetzt (in der Shell exportieren)")
    sys.exit(1)

from nim_nvidia.client import NIMClient, NIMConfig
from nim_nvidia.router import TaskType

async def test():
    config = NIMConfig(
        api_key=key,
        default_max_tokens=256,
        temperature=0.3,
    )
    results = {}

    async with NIMClient(config=config) as nvidia:
        # Test 1: Coding -> DeepSeek V4-Pro
        print("=" * 60)
        print("TEST 1: CODING -> DeepSeek V4-Pro")
        print("=" * 60)
        result = await nvidia.chat_blocking(
            "Schreib eine Python-Funktion, die prüft ob eine Zahl eine Primzahl ist",
            task_type=TaskType.CODING,
        )
        results["coding"] = result
        print(f"Response ({len(result)} Zeichen):")
        print(result[:300])
        print("...")

        # Test 2: Reasoning -> GLM-5.2
        print("\n" + "=" * 60)
        print("TEST 2: REASONING -> GLM-5.2")
        print("=" * 60)
        result2 = await nvidia.chat_blocking(
            "Analysiere die Vor- und Nachteile von SQLite vs PostgreSQL für ein Kleingewerbe",
            task_type=TaskType.REASONING,
        )
        results["reasoning"] = result2
        print(f"Response ({len(result2)} Zeichen):")
        print(result2[:300])
        print("...")

        # Test 3: Long Context -> Nemotron 3 Ultra
        print("\n" + "=" * 60)
        print("TEST 3: LONG_CONTEXT -> Nemotron 3 Ultra")
        print("=" * 60)
        result3 = await nvidia.chat_blocking(
            "Fasse die wichtigsten steuerlichen Pflichten eines Kleinunternehmers in DE zusammen",
            task_type=TaskType.LONG_CONTEXT,
        )
        results["long_context"] = result3
        print(f"Response ({len(result3)} Zeichen):")
        print(result3[:300])
        print("...")

        # Monitoring-Report
        print("\n" + "=" * 60)
        print("MONITORING REPORT")
        print("=" * 60)
        print(nvidia.monitor.get_model_summary_text())

    return results

try:
    results = asyncio.run(test())
    print("\n✅ ALLE 3 TESTS BESTANDEN")
except Exception as e:
    print(f"\n❌ FEHLER: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)