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
        await c.post("/api/sessions", json={"session_id": "t2", "user_id": "test-benign-user", "mode": "text"})
        await c.post("/api/sessions/t2/turns", json={"speaker": "caller", "text": "Mummy, fees aaj bharni hai, 4000 bhej do please."})
        await c.post("/api/sessions/t2/analyze")
        r = await c.post("/api/payments", json={"session_id": "t2", "vpa": "kaushal.rentals@rakshakdemo", "payee_name": "Known payee", "amount_inr": 4000})
        assert r.json()["case"]["decision"]["action"] in ("proceed", "warn")


@pytest.mark.asyncio
async def test_healthz():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/health")
        assert r.status_code == 200 and r.json()["ok"] is True


@pytest.mark.asyncio
async def test_payment_after_hanging_up_uses_carried_over_call_risk():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.post("/api/sessions", json={"session_id": "t3-call", "user_id": "demo-user", "mode": "text"})
        for text in [
            "I am inspector from CBI Mumbai. A parcel with drugs was found in your name. Your arrest warrant is ready.",
            "Do not tell anyone. Transfer the money to the RBI safe account for verification right now, you will get a refund.",
        ]:
            await c.post("/api/sessions/t3-call/turns", json={"speaker": "caller", "text": text})
        r = await c.post("/api/sessions/t3-call/analyze")
        assert r.json()["risk_score"] >= 0.85
        await c.post("/api/sessions/t3-call/end")
        # The customer hangs up and opens the pay screen in a fresh session (new app launch).
        await c.post("/api/sessions", json={"session_id": "t3-pay", "user_id": "demo-user", "mode": "text"})
        r = await c.post("/api/payments", json={"session_id": "t3-pay", "vpa": "cbi.verification@rakshakdemo", "payee_name": "CBI Verification Cell", "amount_inr": 200000})
        case = r.json()["case"]
        assert case["carryover"] is not None and case["carryover"]["from_session"] == "t3-call"
        assert case["decision"]["action"] in ("hold", "hold_and_alert")
        assert any("ended" in x for x in case["rubric"]["reasons"])


@pytest.mark.asyncio
async def test_known_low_risk_payee_after_scam_call_is_at_most_a_warning():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.post("/api/sessions", json={"session_id": "t4-call", "user_id": "test-carry-user", "mode": "text"})
        await c.post("/api/sessions/t4-call/turns", json={"speaker": "caller", "text": "I am inspector from CBI. Arrest warrant ready. Transfer to the RBI safe account now, do not tell anyone."})
        await c.post("/api/sessions/t4-call/analyze")
        await c.post("/api/sessions/t4-call/end")
        await c.post("/api/sessions", json={"session_id": "t4-pay", "user_id": "test-carry-user", "mode": "text"})
        r = await c.post("/api/payments", json={"session_id": "t4-pay", "vpa": "kaushal.rentals@rakshakdemo", "payee_name": "Known payee", "amount_inr": 4000})
        case = r.json()["case"]
        assert case["carryover"] and case["carryover"].get("capped_for_low_risk_payee")
        assert case["decision"]["action"] in ("proceed", "warn")
