"""Live smoke test of the whole decision path with real Gemini + ADK (no browser needed).
Usage: uv run python scripts/smoke_agent.py [--benign]"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from app.config import configure_env, settings  # noqa: E402
from app.payment import evaluate_payment  # noqa: E402
from app.session import registry  # noqa: E402
from app.store import store  # noqa: E402

SCAM = [
    ("caller", "नमस्ते, मैं CBI मुंबई से इंस्पेक्टर राठौड़ बोल रहा हूँ। आपके नाम से एक पार्सल में ड्रग्स पकड़े गए हैं।"),
    ("user", "क्या? मैंने तो कुछ नहीं भेजा।"),
    ("caller", "देखिए, आपका गिरफ्तारी वारंट तैयार है। किसी को मत बताइए, यह राष्ट्रीय सुरक्षा का मामला है। कॉल मत काटिए।"),
    ("caller", "बचने के लिए आपको अपना पैसा RBI के सेफ अकाउंट में ट्रांसफर करना होगा, जाँच के बाद वापस मिल जाएगा। अभी UPI से 2 लाख cbi.verification@rakshakdemo पर भेजिए।"),
]
BENIGN = [
    ("caller", "Mummy, main Priya bol rahi hoon. College ki fees aaj last date hai, 40000 bhej do please, abhi."),
    ("user", "Theek hai beta, bhej rahi hoon."),
]


async def main() -> None:
    configure_env()
    benign = "--benign" in sys.argv
    print("llm enabled:", settings.llm_enabled(), "| rubric model:", settings.model_rubric, "| agent model:", settings.model_agent)
    s = registry.get_or_create("smoke-" + str(int(time.time())), user_id="demo-user", mode="text")
    for sp, text in (BENIGN if benign else SCAM):
        await s.add_turn(sp, text, analyse=False)
    t0 = time.time()
    r = await s.run_analysis()
    print(f"\n[rubric {int((time.time()-t0)*1000)} ms] risk={r.risk_score} type={r.scam_type} stage={r.stage} lang={r.language}")
    print("  signals:", [k for k, v in r.signals.items() if v])
    print("  reasons (user lang):", r.reasons_user_language)
    t0 = time.time()
    if benign:
        res = await evaluate_payment(s, "priya.sharma@rakshakdemo", "Priya Sharma", 40000, use_agent=True)
    else:
        res = await evaluate_payment(s, "cbi.verification@rakshakdemo", "CBI Verification Cell", 200000, use_agent=True)
    c = res["case"]
    print(f"\n[payment {int((time.time()-t0)*1000)} ms] action={c['decision']['action']} by={c['decision']['decided_by']} conf={c['decision']['confidence']} status={c['status']}")
    print("  policy:", c["policy"]["action"], c["policy"]["score"])
    print("  payee:", c["payee"].get("risk_band"), c["payee"].get("mule_risk_score"), c["payee"].get("source"))
    print("  reasons:", c["decision"]["reasons"])
    print("  user_message:", c["decision"]["user_message"][:300])
    print("  spoken audio bytes:", len(res["audio_b64"] or "") * 3 // 4)
    print("  alert:", (c.get("alert") or {}).get("channels"))
    # wait for the background agent + narrative
    for _ in range(90):
        case = store().get_case(c["case_id"])
        if case["decision"].get("agent_status") not in ("pending",) and case.get("narrative"):
            break
        await asyncio.sleep(1)
    case = store().get_case(c["case_id"])
    d = case["decision"]
    print(f"\n[agent] status={d.get('agent_status')} by={d.get('decided_by')} action={d['action']} agent_action={d.get('agent_action')} model={d.get('model')} latency={d.get('latency_ms')} ms")
    print("  reasons:", d["reasons"])
    print("  user_message:", d["user_message"][:300])
    print("\n[trace]")
    for e in case["trace"]:
        if e["type"] == "tool_call":
            print(f"  {e['agent']:18} CALL  {e['name']}({json.dumps(e['args'], ensure_ascii=False)[:140]})")
        elif e["type"] == "tool_result":
            print(f"  {e['agent']:18} RESULT {e['name']} -> {json.dumps(e['result'], ensure_ascii=False)[:160]}")
        elif e["type"] == "text":
            print(f"  {e['agent']:18} TEXT  {e['text'][:220]!r}")
        else:
            print(f"  {e['agent']:18} {e['type']} {e.get('text','')[:200]}")
    n = case.get("narrative")
    print("\n[narrative]", (n or {}).get("narrative", "(pending)")[:500])
    print("[referral]", (n or {}).get("referral_text", "")[:300])


if __name__ == "__main__":
    asyncio.run(main())
