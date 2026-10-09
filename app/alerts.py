"""Trusted-contact alerts: Pub/Sub (production fan-out), in-app feed (always), Twilio SMS (optional)."""
from __future__ import annotations

import json
import logging
import time

import httpx

from .config import settings
from .store import store

log = logging.getLogger("rakshak.alerts")


def _publish_pubsub(payload: dict) -> bool:  # pragma: no cover - needs GCP
    if not settings.pubsub_topic:
        return False
    try:
        from google.cloud import pubsub_v1

        publisher = pubsub_v1.PublisherClient()
        topic = settings.pubsub_topic
        if not topic.startswith("projects/"):
            topic = publisher.topic_path(settings.project, topic)
        publisher.publish(topic, json.dumps(payload).encode("utf-8"), event_type="trusted_contact_alert").result(timeout=10)
        return True
    except Exception as e:
        log.warning("Pub/Sub publish failed: %s", str(e)[:120])
        return False


async def _send_twilio_sms(to: str, body: str) -> bool:  # pragma: no cover - needs Twilio
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_from_number):
        return False
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(url, data={"From": settings.twilio_from_number, "To": to, "Body": body},
                             auth=(settings.twilio_account_sid, settings.twilio_auth_token))
            return r.status_code in (200, 201)
    except Exception as e:
        log.warning("Twilio SMS failed: %s", str(e)[:120])
        return False


async def notify_trusted_contact(case: dict, profile: dict) -> dict:
    contact = profile.get("trusted_contact_name") or "trusted contact"
    phone = profile.get("trusted_contact_phone")
    body = (
        f"Rakshak alert: {profile.get('name', 'your family member')} tried to send "
        f"₹{case['payment']['amount_inr']:,.0f} to {case['payment']['vpa']} during a call that looks like a "
        f"{case['rubric'].get('scam_type', 'scam').replace('_', ' ')} scam. The payment is on hold for "
        f"{case['decision'].get('hold_minutes', settings.hold_minutes)} minutes. Please call them now."
    )
    payload = {
        "alert_id": f"alert_{int(time.time() * 1000)}",
        "case_id": case["case_id"],
        "user_id": case["user_id"],
        "contact_name": contact,
        "contact_phone": phone,
        "message": body,
        "created_at": time.time(),
        "channels": ["in_app"],
    }
    if _publish_pubsub(payload):
        payload["channels"].append("pubsub")
    if phone and await _send_twilio_sms(phone, body):
        payload["channels"].append("sms")
    store().add_alert(payload)
    return payload
