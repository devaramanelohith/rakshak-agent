import os

os.environ["RAKSHAK_FAKE_LLM"] = "1"

from app.analysis import stub_rubric  # noqa: E402
from app.audio import mulaw_to_pcm16, pcm16_to_mulaw, resample_pcm16  # noqa: E402
from app.policy import fuse  # noqa: E402

SCAM_TURNS = [
    {"t": 0, "speaker": "caller", "text": "I am inspector from CBI Mumbai. A parcel with drugs was found in your name."},
    {"t": 20, "speaker": "caller", "text": "Your arrest warrant is ready. Do not tell anyone, national security matter."},
    {"t": 40, "speaker": "caller", "text": "Transfer the money to the RBI safe account for verification immediately, you will get a refund."},
]
BENIGN_TURNS = [
    {"t": 0, "speaker": "caller", "text": "Mummy, college fees are due today, can you send 40000 to my UPI? Please do it right now."},
    {"t": 10, "speaker": "user", "text": "Theek hai beta, bhej rahi hoon."},
]
MULE = {"mule_risk_score": 0.93, "risk_band": "critical", "linked_complaints_1930": 4}
CLEAN = {"mule_risk_score": 0.05, "risk_band": "low", "linked_complaints_1930": 0}
PROFILE = {"trusted_contact_name": "Priya", "typical_transfer_inr": 4000}


def test_stub_rubric_detects_digital_arrest():
    r = stub_rubric(SCAM_TURNS)
    assert r.signals["authority_impersonation"] and r.signals["safe_account"] and r.signals["secrecy"]
    assert r.risk_score >= 0.85 and r.scam_type == "digital_arrest"


def test_stub_rubric_benign_urgency_is_low():
    r = stub_rubric(BENIGN_TURNS)
    assert r.risk_score < 0.45


def test_fusion_holds_and_alerts_on_scam_with_mule_payee():
    r = stub_rubric(SCAM_TURNS)
    f = fuse(r.risk_score, r.signals, MULE, 200000, PROFILE)
    assert f.action == "hold_and_alert" and f.score >= 0.9


def test_fusion_proceeds_for_benign_urgent_family_payment():
    r = stub_rubric(BENIGN_TURNS)
    f = fuse(r.risk_score, r.signals, CLEAN, 40000, PROFILE)
    assert f.action in ("proceed", "warn")


def test_fusion_without_trusted_contact_is_plain_hold():
    r = stub_rubric(SCAM_TURNS)
    f = fuse(r.risk_score, r.signals, MULE, 200000, {"typical_transfer_inr": 4000})
    assert f.action == "hold"


def test_resample_lengths():
    pcm = (b"\x00\x10" * 2400)  # 100 ms @ 24 kHz
    out = resample_pcm16(pcm, 24000, 16000)
    assert abs(len(out) - 3200) <= 4


def test_mulaw_roundtrip_is_close():
    import numpy as np

    x = (np.sin(np.linspace(0, 40, 800)) * 12000).astype(np.int16).tobytes()
    y = np.frombuffer(mulaw_to_pcm16(pcm16_to_mulaw(x)), dtype=np.int16)
    xx = np.frombuffer(x, dtype=np.int16)
    assert np.mean(np.abs(y.astype(int) - xx.astype(int))) < 400
