"""WebSocket smoke test against a running server (default http://127.0.0.1:8080):
transcript-driven scam call -> Pay -> time-to-hold-event and time-to-voice -> post-hold Live conversation (typed).
Usage: uv run python scripts/smoke_ws.py [base_url]"""
from __future__ import annotations

import asyncio
import json
import sys
import time

import httpx
import websockets

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
WS = BASE.replace("http", "ws", 1)
TURNS = [
    ("caller", "नमस्ते, मैं CBI मुंबई से इंस्पेक्टर बोल रहा हूँ। आपके नाम से एक पार्सल में ड्रग्स पकड़े गए हैं।"),
    ("user", "क्या? मैंने कुछ नहीं भेजा।"),
    ("caller", "आपका गिरफ्तारी वारंट तैयार है। किसी को मत बताइए, यह राष्ट्रीय सुरक्षा का मामला है।"),
    ("caller", "अभी RBI के सेफ अकाउंट cbi.verification@rakshakdemo पर 2 लाख UPI से भेजिए, जाँच के बाद वापस मिल जाएगा।"),
]


async def main() -> None:
    sid = f"ws-{int(time.time())}"
    async with httpx.AsyncClient(base_url=BASE, timeout=60) as http:
        await http.post("/api/sessions", json={"session_id": sid, "user_id": "demo-user", "mode": "text"})
        events: list[tuple[float, dict]] = []
        audio_msgs: list[tuple[float, str]] = []

        async def ev_reader(ws):
            async for m in ws:
                events.append((time.time(), json.loads(m)))

        async def call_reader(ws):
            async for m in ws:
                if isinstance(m, str):
                    d = json.loads(m)
                    if d.get("type") == "rakshak_audio":
                        audio_msgs.append((time.time(), f"{d.get('kind')} {len(d.get('audio_b64') or '') * 3 // 4} bytes"))

        async with websockets.connect(f"{WS}/ws/events/{sid}") as evws, websockets.connect(f"{WS}/ws/call/{sid}/user", max_size=None) as callws:
            t_ev = asyncio.create_task(ev_reader(evws))
            t_call = asyncio.create_task(call_reader(callws))
            for sp, text in TURNS:
                await http.post(f"/api/sessions/{sid}/turns", json={"speaker": sp, "text": text})
            t0 = time.time()
            r = await http.post(f"/api/sessions/{sid}/analyze")
            print(f"rubric: risk={r.json()['risk_score']} in {time.time()-t0:.1f}s")
            await http.post(f"/api/sessions/{sid}/prewarm", params={"amount_inr": 200000})
            await asyncio.sleep(8)  # let prewarm finish (first time only)
            t0 = time.time()
            r = await http.post("/api/payments", json={"session_id": sid, "vpa": "cbi.verification@rakshakdemo", "payee_name": "CBI Verification Cell", "amount_inr": 200000})
            t_http = time.time() - t0
            case = r.json()["case"]
            dec = next((t for t, e in events if e.get("type") == "decision"), None)
            print(f"POST /api/payments returned in {t_http:.1f}s -> {case['decision']['action']} by {case['decision']['decided_by']} agent_status={case['decision'].get('agent_status')}")
            print(f"  decision event after {dec - t0:.2f}s" if dec else "  decision event: NOT received")
            await asyncio.sleep(3)
            print("  voice messages:", [(f"+{t - t0:.1f}s", s) for t, s in audio_msgs] or "none")
            for _ in range(60):
                upd = [e for _, e in events if e.get("type") == "case_update" and e.get("agent")]
                if upd:
                    d = upd[-1]["case"]["decision"]
                    print(f"  agent update after {[t for t, e in events if e is upd[-1]][0] - t0:.1f}s: {d['action']} status={d.get('agent_status')} model={d.get('model')} latency={d.get('latency_ms')} ms")
                    break
                await asyncio.sleep(1)
            else:
                print("  agent update: not received within 60s")
            t_ev.cancel(); t_call.cancel()

        # ---- post-hold Live conversation (typed input instead of mic) ----
        cid = case["case_id"]
        audio = 0; texts: list[str] = []; tools: list[str] = []; errs: list[str] = []
        try:
            async with websockets.connect(f"{WS}/ws/guardian/{cid}", max_size=None) as g:
                async def reader():
                    nonlocal audio
                    async for m in g:
                        if isinstance(m, bytes):
                            audio += len(m)
                        else:
                            d = json.loads(m)
                            if d.get("type") == "guardian_text": texts.append(d["text"])
                            elif d.get("type") == "tool": tools.append(d["name"])
                            elif d.get("type") == "error": errs.append(d["error"])
                rt = asyncio.create_task(reader())
                await asyncio.sleep(8)
                await g.send(json.dumps({"type": "text", "text": "आपने मेरा पेमेंट क्यों रोका? मुझे डर लग रहा है।"}))
                await asyncio.sleep(12)
                await g.send(json.dumps({"type": "text", "text": "ठीक है, पेमेंट रोके रखिए और मेरी बेटी को फ़ोन कीजिए।"}))
                await asyncio.sleep(12)
                await g.send(json.dumps({"type": "end"}))
                await asyncio.sleep(1)
                rt.cancel()
        except Exception as e:
            errs.append(f"{type(e).__name__}: {str(e)[:160]}")
        print(f"guardian voice: audio_bytes={audio} tools={tools} errors={errs}")
        print("rakshak said:", "".join(texts)[:600])


if __name__ == "__main__":
    asyncio.run(main())
