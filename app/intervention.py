"""What Rakshak says, in the user's language, and how it is voiced (Gemini TTS with a disk cache so the
barge-in is instant during a demo)."""
from __future__ import annotations

import hashlib
import logging

from google.genai import types

from .audio import read_wav, resample_pcm16, wav_bytes
from .config import settings
from .llm import client

log = logging.getLogger("rakshak.intervention")

# Templates keyed by language. {payee}, {amount}, {contact}, {minutes}
HOLD_SCRIPTS = {
    "hi": "रुकिए। मैं रक्षक हूँ, आपके बैंक का सुरक्षा सहायक। कोई भी पुलिस, सीबीआई या आरबीआई अधिकारी यूपीआई से पैसा नहीं माँगता। जिस खाते में आप {amount} भेज रहे हैं, उसमें पिछले दो दिनों में कई लोगों से पैसा आया है और तुरंत निकाला गया है। मैंने यह भुगतान {minutes} मिनट के लिए रोक दिया है और {contact} को सूचना भेज दी है। आप सुरक्षित हैं। कृपया यह कॉल काट दें।",
    "en": "Please stop. I am Rakshak, your bank's safety assistant. No police, CBI or RBI officer ever asks for money over UPI. The account you are sending {amount} to received money from many people in the last two days and emptied it immediately. I have paused this payment for {minutes} minutes and notified {contact}. You are safe. Please hang up this call.",
    "en-sg": "Please stop. I am Rakshak, your bank's safety assistant. No government officer, police or MAS official will ever ask you to transfer money by PayNow. The account you are paying {amount} to received money from many people in the last two days and emptied it immediately. I have paused this payment for {minutes} minutes and notified {contact}. You are safe. Please hang up.",
    "kn": "ದಯವಿಟ್ಟು ನಿಲ್ಲಿಸಿ. ನಾನು ರಕ್ಷಕ್, ನಿಮ್ಮ ಬ್ಯಾಂಕಿನ ಸುರಕ್ಷತಾ ಸಹಾಯಕ. ಯಾವುದೇ ಪೊಲೀಸ್, ಸಿಬಿಐ ಅಥವಾ ಆರ್‌ಬಿಐ ಅಧಿಕಾರಿ ಯುಪಿಐ ಮೂಲಕ ಹಣ ಕೇಳುವುದಿಲ್ಲ. ನೀವು {amount} ಕಳುಹಿಸುತ್ತಿರುವ ಖಾತೆಗೆ ಕಳೆದ ಎರಡು ದಿನಗಳಲ್ಲಿ ಹಲವರಿಂದ ಹಣ ಬಂದು ತಕ್ಷಣ ಖಾಲಿಯಾಗಿದೆ. ನಾನು ಈ ಪಾವತಿಯನ್ನು {minutes} ನಿಮಿಷ ತಡೆಹಿಡಿದಿದ್ದೇನೆ ಮತ್ತು {contact} ಅವರಿಗೆ ತಿಳಿಸಿದ್ದೇನೆ. ನೀವು ಸುರಕ್ಷಿತವಾಗಿದ್ದೀರಿ. ದಯವಿಟ್ಟು ಕರೆ ಕಡಿತಗೊಳಿಸಿ.",
    "ta": "தயவுசெய்து நிறுத்துங்கள். நான் ரக்ஷக், உங்கள் வங்கியின் பாதுகாப்பு உதவியாளர். எந்த காவல்துறை, சிபிஐ அல்லது ஆர்பிஐ அதிகாரியும் யுபிஐ மூலம் பணம் கேட்க மாட்டார்கள். நீங்கள் {amount} அனுப்பும் கணக்கிற்கு கடந்த இரண்டு நாட்களில் பலரிடமிருந்து பணம் வந்து உடனே எடுக்கப்பட்டுள்ளது. இந்தப் பணப்பரிமாற்றத்தை {minutes} நிமிடங்களுக்கு நிறுத்தி {contact} அவர்களுக்குத் தகவல் அனுப்பியுள்ளேன். நீங்கள் பாதுகாப்பாக இருக்கிறீர்கள். தயவுசெய்து அழைப்பைத் துண்டியுங்கள்.",
}
HOLD_SCRIPTS["hinglish"] = "Rukiye. Main Rakshak hoon, aapke bank ka safety assistant. Koi bhi police, CBI ya RBI officer UPI se paisa nahi maangta. Jis account mein aap {amount} bhej rahe hain, usme pichhle do din mein kai logon se paisa aaya aur turant nikaal liya gaya. Maine yeh payment {minutes} minute ke liye rok diya hai aur {contact} ko inform kar diya hai. Aap surakshit hain. Please yeh call kaat dijiye."

WARN_SCRIPTS = {
    "hi": "एक पल रुकिए। इस कॉल में कुछ संकेत हैं जो आम तौर पर धोखाधड़ी में दिखते हैं। क्या आप इस व्यक्ति को व्यक्तिगत रूप से जानते हैं? अगर नहीं, तो भुगतान से पहले {contact} से बात कर लीजिए।",
    "en": "One moment. This call shows some signs we usually see in scams. Do you personally know this person? If not, please talk to {contact} before paying.",
    "en-sg": "One moment. This call shows some signs we usually see in scams. Do you personally know this person? If not, please check with {contact} before paying.",
}
WARN_SCRIPTS["hinglish"] = "Ek pal rukiye. Is call mein kuch aise sanket hain jo aam taur par fraud mein dikhte hain. Kya aap is vyakti ko jaante hain? Agar nahi, to payment se pehle {contact} se baat kar lijiye."

WHISPER_SCRIPTS = {
    "hi": "रक्षक: सावधान। यह कॉल धोखाधड़ी जैसी लग रही है। कोई अधिकारी फ़ोन पर पैसा नहीं माँगता।",
    "en": "Rakshak here: careful. This call looks like a scam. No officer asks for money on a call.",
    "en-sg": "Rakshak here: careful. This call looks like a scam. No government officer asks for money on a call.",
    "kn": "ರಕ್ಷಕ್: ಎಚ್ಚರ. ಈ ಕರೆ ವಂಚನೆಯಂತೆ ಕಾಣುತ್ತಿದೆ. ಯಾವ ಅಧಿಕಾರಿಯೂ ಕರೆಯಲ್ಲಿ ಹಣ ಕೇಳುವುದಿಲ್ಲ.",
    "ta": "ரக்ஷக்: கவனம். இந்த அழைப்பு மோசடி போல் தெரிகிறது. எந்த அதிகாரியும் அழைப்பில் பணம் கேட்க மாட்டார்.",
}
WHISPER_SCRIPTS["hinglish"] = "Rakshak: saavdhan. Yeh call fraud jaisi lag rahi hai. Koi officer phone par paisa nahi maangta."


def _lang(profile: dict | None) -> str:
    lang = (profile or {}).get("language") or "en"
    return lang if lang in HOLD_SCRIPTS else ("en" if lang.startswith("en") else "en")


def fmt_amount(amount_inr: float, lang: str) -> str:
    if lang == "en-sg":
        return f"S${amount_inr:,.0f}"
    if amount_inr >= 100000:
        lakhs = amount_inr / 100000
        return (f"{lakhs:g} लाख रुपये" if lang == "hi" else f"{lakhs:g} lakh rupees")
    return f"₹{amount_inr:,.0f}"


def compose(action: str, profile: dict | None, amount_inr: float, minutes: int) -> tuple[str, str]:
    lang = _lang(profile)
    contact = (profile or {}).get("trusted_contact_name") or ("आपके परिवार" if lang == "hi" else "your family")
    kw = dict(amount=fmt_amount(amount_inr, lang), contact=contact, minutes=minutes)
    if action in ("hold", "hold_and_alert"):
        return lang, HOLD_SCRIPTS[lang].format(**kw)
    if action == "warn":
        return lang, WARN_SCRIPTS.get(lang, WARN_SCRIPTS["en"]).format(**kw)
    return lang, ""


def whisper_text(profile: dict | None) -> tuple[str, str]:
    lang = _lang(profile)
    return lang, WHISPER_SCRIPTS.get(lang, WHISPER_SCRIPTS["en"])


_mem_cache: dict[str, bytes] = {}


async def tts_pcm16(text: str, voice: str | None = None, rate: int = 16000) -> bytes:
    """Return mono PCM16 at `rate` for `text`. Cached on disk (data/tts_cache) and in memory."""
    voice = voice or settings.tts_voice_guardian
    key = hashlib.sha1(f"{settings.model_tts}|{voice}|{rate}|{text}".encode()).hexdigest()
    if key in _mem_cache:
        return _mem_cache[key]
    path = settings.tts_cache_dir / f"{key}.wav"
    if path.exists():
        pcm, r = read_wav(path.read_bytes())
        pcm = resample_pcm16(pcm, r, rate)
        _mem_cache[key] = pcm
        return pcm
    if not settings.llm_enabled():
        return b""
    cfg = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice))),
    )
    resp = await client().aio.models.generate_content(model=settings.model_tts, contents=text, config=cfg)
    part = resp.candidates[0].content.parts[0]
    data, mime = part.inline_data.data, part.inline_data.mime_type or ""
    if mime.startswith("audio/wav") or data[:4] == b"RIFF":
        pcm, src_rate = read_wav(data)
    else:
        src_rate = int(mime.split("rate=")[1]) if "rate=" in mime else 24000
        pcm = data
    path.write_bytes(wav_bytes(pcm, src_rate))
    pcm = resample_pcm16(pcm, src_rate, rate)
    _mem_cache[key] = pcm
    return pcm


async def prewarm_amount(profile: dict, amount_inr: float) -> int:
    n = 0
    for action in ("hold_and_alert", "warn"):
        _, text = compose(action, profile, amount_inr, settings.hold_minutes)
        if text:
            await tts_pcm16(text)
            n += 1
    return n


async def prewarm(profiles: list[dict], amounts: list[float] = (200000, 50000)) -> int:
    """Pre-generate the hold/warn/whisper audio for the demo profiles so the barge-in has zero latency."""
    n = 0
    for prof in profiles:
        for action in ("hold_and_alert", "warn"):
            for amt in amounts:
                _, text = compose(action, prof, amt, settings.hold_minutes)
                if text:
                    await tts_pcm16(text)
                    n += 1
        _, w = whisper_text(prof)
        await tts_pcm16(w)
        n += 1
    return n
