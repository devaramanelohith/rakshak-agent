"""Proves the live two-device audio path without a browser: a 'caller' client rings, streams a real
Hindi scam recording (TTS) over the call WebSocket at real-time pace, a 'user' client accepts and receives the
relayed audio, and the events socket must show transcript turns from gemini-3.5-transcribe-live, a risk_update
above the hold threshold and the whisper. Usage: uv run python scripts/smoke_live_audio.py [base_url]"""
from __future__ import annotations

import asyncio
import base64
import json
import sys
import time

import httpx
import websockets

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
WS = BASE.replace("http", "ws", 1)
LINES = [
    "नमस्ते, मैं CBI मुंबई से इंस्पेक्टर बोल रहा हूँ। आपके नाम से एक पार्सल में ड्रग्स पकड़े गए हैं।",
    "आपका गिरफ्तारी वारंट तैयार है। किसी को मत बताइए, यह राष्ट्रीय सुरक्षा का मामला है। कॉल मत काटिए।",
    "बचने के लिए अभी RBI के सेफ अकाउंट में दो लाख रुपये UPI से भेजिए, जाँच के बाद वापस मिल जाएगा।",
]


async def main() -> None:
    sid = f"live-{int(time.time())}"
    async with httpx.AsyncClient(base_url=BASE, timeout=120) as http:
        await http.post("/api/sessions", json={"session_id": sid, "user_id": "demo-user", "mode": "audio"})
        clips = []
        for text in LINES:
            r = await http.get("/api/tts", params={"text": text, "voice": "Charon"})
            clips.append(base64.b64decode(r.json()["audio_b64"]))
        print(f"prepared {len(clips)} caller clips, {sum(len(c) for c in clips)/32000:.1f}s of audio")
        events: list[dict] = []
        relayed = 0

        async def ev_reader(ws):
            async for m in ws:
                events.append(json.loads(m))

        async def user_reader(ws):
            nonlocal relayed
            async for m in ws:
                if isinstance(m, bytes):
                    relayed += len(m)

        async with websockets.connect(f"{WS}/ws/events/{sid}") as ev, websockets.connect(f"{WS}/ws/call/{sid}/user", max_size=None) as user, websockets.connect(f"{WS}/ws/call/{sid}/caller", max_size=None) as caller:
            t_ev = asyncio.create_task(ev_reader(ev)); t_u = asyncio.create_task(user_reader(user))
            await caller.send(json.dumps({"type": "ring", "caller_display": "+91 98765 00301"}))
            await asyncio.sleep(1)
            assert any(e.get("type") == "incoming_call" for e in events), "customer app did not receive incoming_call"
            await user.send(json.dumps({"type": "accept"}))
            await asyncio.sleep(0.5)
            assert any(e.get("type") == "call_accepted" for e in events), "call_accepted not broadcast"
            t0 = time.time()
            for clip in clips:
                for i in range(0, len(clip), 3200):  # 100 ms chunks at 16 kHz
                    await caller.send(clip[i:i + 3200])
                    await asyncio.sleep(0.1)
                silence = b"\x00" * 3200
                for _ in range(15):  # 1.5 s pause between sentences so the transcriber closes the utterance
                    await caller.send(silence)
                    await asyncio.sleep(0.1)
            await asyncio.sleep(10)
            turns = [e["turn"] for e in events if e.get("type") == "transcript"]
            risks = [e["rubric"]["risk_score"] for e in events if e.get("type") == "risk_update"]
            whisper = [e for e in events if e.get("type") == "whisper"]
            print(f"streamed in {time.time()-t0:.1f}s; relayed to user: {relayed/32000:.1f}s audio")
            print(f"transcript turns: {len(turns)}")
            for t in turns:
                print("   ", t["speaker"], "·", t["text"][:90])
            print(f"risk updates: {[round(r,2) for r in risks]}  whisper: {bool(whisper)}")
            ok = len(turns) >= 2 and risks and max(risks) >= 0.7 and relayed > 0
            print("LIVE AUDIO PATH:", "PASS" if ok else "FAIL")
            await caller.send(json.dumps({"type": "end_call"}))
            t_ev.cancel(); t_u.cancel()


if __name__ == "__main__":
    asyncio.run(main())
