import os

os.environ["RAKSHAK_FAKE_LLM"] = "1"
os.environ["RAKSHAK_PREWARM_TTS"] = "0"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.mark.asyncio
async def test_end_to_end_scam_hold_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/sessions", json={"session_id": "t1", "user_id": "demo-user", "mode": "text"})
        assert r.status_code == 200
        for text in [
            "Main CBI Mumbai se inspector bol raha hoon, aapke naam se parcel mein drugs pakde gaye hain.",
            "Aapka arrest warrant ready hai. Kisi ko mat batao, national security ka matter hai.",
            "Bachne ke liye abhi RBI ke safe account mein 2 lakh UPI se transfer karo, verification ke baad refund milega.",
        ]:
            r = await c.post("/api/sessions/t1/turns", json={"speaker": "caller", "text": text})
            assert r.status_code == 200
        r = await c.post("/api/sessions/t1/analyze")
        assert r.json()["risk_score"] >= 0.85
        r = await c.post("/api/payments", json={"session_id": "t1", "vpa": "cbi.verification@rakshakdemo", "payee_name": "CBI Verification", "amount_inr": 200000})
        assert r.status_code == 200, r.text
        case = r.json()["case"]
        assert case["decision"]["action"] in ("hold", "hold_and_alert")
        assert case["status"] == "on_hold"
        r = await c.post(f"/api/cases/{case['case_id']}/override", json={"reason": "test"})
        assert r.json()["status"] == "overridden_by_user"
        r = await c.get("/api/cases")
        assert any(x["case_id"] == case["case_id"] for x in r.json())


@pytest.mark.asyncio
async def test_benign_payment_proceeds():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.post("/api/sessions", json={"session_id": "t2", "user_id": "demo-user", "mode": "text"})
        await c.post("/api/sessions/t2/turns", json={"speaker": "caller", "text": "Mummy, fees aaj bharni hai, 4000 bhej do please."})
        await c.post("/api/sessions/t2/analyze")
        r = await c.post("/api/payments", json={"session_id": "t2", "vpa": "priya.sharma@rakshakdemo", "payee_name": "Priya", "amount_inr": 4000})
        assert r.json()["case"]["decision"]["action"] in ("proceed", "warn")


@pytest.mark.asyncio
async def test_healthz():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/healthz")
        assert r.status_code == 200 and r.json()["ok"] is True
