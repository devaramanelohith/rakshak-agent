// SafePay customer app with the Rakshak guardian. State: session, websockets, audio, onboarding, drill.
const S = { sid: null, userId: 'demo-user', profile: null, evWS: null, evGen: 0, callWS: null, mic: null, callStart: null, timer: null, callActive: false,
            caller: new Player(), guardian: new Player(), lastRubric: null, case: null, countdownT: null, guardianWS: null, guardianMic: null, guardianPlayer: new Player(),
            replayPayment: null, holdAudio: null, scripts: [], talkReady: false };
const D = { active: false, script: null, queue: [], answers: [], lastRubric: null, benign: false };
const $ = (id) => document.getElementById(id);
const ONBOARD_KEY = () => `rakshak.onboarded.${S.userId}`;

// ---------- copy in the customer's language ----------
const T = {
  en: { holdTitle: 'Payment paused for your safety', warnTitle: 'Please double-check this payment', sentTitle: 'Payment sent', cancelledTitle: 'Payment cancelled', drillQ: 'What would you do?', hangup: 'Hang up', hangupD: 'End the call now', verify: 'Ask to verify', verifyD: 'Say you will call the official number or your family first', comply: 'Do what they say', complyD: 'Follow the caller’s instructions', listening: 'Rakshak is listening', coachTitle: 'What Rakshak noticed in this call', good: 'Good choice', ok: 'Safer than complying', bad: 'Risky' },
  hi: { holdTitle: 'आपकी सुरक्षा के लिए भुगतान रोका गया', warnTitle: 'कृपया इस भुगतान की दोबारा जाँच करें', sentTitle: 'भुगतान भेज दिया गया', cancelledTitle: 'भुगतान रद्द', drillQ: 'आप क्या करेंगे?', hangup: 'कॉल काट दें', hangupD: 'अभी कॉल खत्म करें', verify: 'पहले जाँच करें', verifyD: 'कहें कि आप आधिकारिक नंबर या परिवार से पहले बात करेंगे', comply: 'जैसा कहा जाए वैसा करें', complyD: 'कॉलर के निर्देश मानें', listening: 'रक्षक सुन रहा है', coachTitle: 'इस कॉल में रक्षक ने क्या देखा', good: 'सही फ़ैसला', ok: 'मानने से सुरक्षित', bad: 'जोखिम भरा' },
  hinglish: { holdTitle: 'Aapki suraksha ke liye payment roka gaya', warnTitle: 'Please is payment ko dobara check karein', sentTitle: 'Payment bhej diya gaya', cancelledTitle: 'Payment cancel', drillQ: 'Aap kya karenge?', hangup: 'Call kaat dein', hangupD: 'Abhi call khatam karein', verify: 'Pehle verify karein', verifyD: 'Kahein ki aap official number ya family se pehle baat karenge', comply: 'Jaisa kaha jaaye waisa karein', complyD: 'Caller ke instructions maanein', listening: 'Rakshak sun raha hai', coachTitle: 'Is call mein Rakshak ne kya dekha', good: 'Sahi faisla', ok: 'Maanne se surakshit', bad: 'Risky' },
  kn: { holdTitle: 'ನಿಮ್ಮ ಸುರಕ್ಷತೆಗಾಗಿ ಪಾವತಿ ತಡೆಹಿಡಿಯಲಾಗಿದೆ', warnTitle: 'ದಯವಿಟ್ಟು ಈ ಪಾವತಿಯನ್ನು ಮತ್ತೊಮ್ಮೆ ಪರಿಶೀಲಿಸಿ', sentTitle: 'ಪಾವತಿ ಕಳುಹಿಸಲಾಗಿದೆ', cancelledTitle: 'ಪಾವತಿ ರದ್ದಾಗಿದೆ', drillQ: 'ನೀವು ಏನು ಮಾಡುತ್ತೀರಿ?', hangup: 'ಕರೆ ಕಡಿತಗೊಳಿಸಿ', hangupD: 'ಈಗಲೇ ಕರೆ ಮುಗಿಸಿ', verify: 'ಮೊದಲು ಪರಿಶೀಲಿಸಿ', verifyD: 'ಅಧಿಕೃತ ಸಂಖ್ಯೆಗೆ ಅಥವಾ ಕುಟುಂಬಕ್ಕೆ ಮೊದಲು ಕರೆ ಮಾಡುವುದಾಗಿ ಹೇಳಿ', comply: 'ಹೇಳಿದಂತೆ ಮಾಡಿ', complyD: 'ಕರೆ ಮಾಡಿದವರ ಸೂಚನೆ ಪಾಲಿಸಿ', listening: 'ರಕ್ಷಕ್ ಕೇಳುತ್ತಿದೆ', coachTitle: 'ಈ ಕರೆಯಲ್ಲಿ ರಕ್ಷಕ್ ಗಮನಿಸಿದ್ದು', good: 'ಸರಿಯಾದ ಆಯ್ಕೆ', ok: 'ಪಾಲಿಸುವುದಕ್ಕಿಂತ ಸುರಕ್ಷಿತ', bad: 'ಅಪಾಯಕಾರಿ' },
  ta: { holdTitle: 'உங்கள் பாதுகாப்பிற்காக பணப்பரிமாற்றம் நிறுத்தப்பட்டது', warnTitle: 'இந்த பணப்பரிமாற்றத்தை மீண்டும் சரிபார்க்கவும்', sentTitle: 'பணம் அனுப்பப்பட்டது', cancelledTitle: 'பணப்பரிமாற்றம் ரத்து', drillQ: 'நீங்கள் என்ன செய்வீர்கள்?', hangup: 'அழைப்பைத் துண்டிக்கவும்', hangupD: 'இப்போதே அழைப்பை முடிக்கவும்', verify: 'முதலில் சரிபார்க்கவும்', verifyD: 'அதிகாரப்பூர்வ எண்ணுக்கோ குடும்பத்தினருக்கோ முதலில் அழைப்பதாகச் சொல்லுங்கள்', comply: 'அவர்கள் சொல்வதைச் செய்யுங்கள்', complyD: 'அழைப்பாளரின் வழிமுறைகளைப் பின்பற்றுங்கள்', listening: 'ரக்ஷக் கேட்டுக்கொண்டிருக்கிறது', coachTitle: 'இந்த அழைப்பில் ரக்ஷக் கவனித்தது', good: 'சரியான முடிவு', ok: 'பின்பற்றுவதை விடப் பாதுகாப்பானது', bad: 'ஆபத்தானது' },
};
const LANG_NAMES = { hi: 'Hindi', hinglish: 'Hinglish', en: 'English', 'en-sg': 'English (Singapore)', kn: 'Kannada', ta: 'Tamil' };
const TIER_TEXT = { 0: 'Privacy tier 0 · no audio, call-state + payee check only', 1: 'Privacy tier 1 · transcript stays on this phone until you pay', 2: 'Privacy tier 2 · cloud analysis (this demo)' };
const LISTEN_TEXT = { 0: 'Call state only', 1: 'On-device transcript', 2: null };
const SIGNAL_LABELS = { authority_impersonation: 'Claims authority', secrecy: 'Demands secrecy', urgency: 'Rushing you', remote_app_install: 'Screen-share app', safe_account: '“Safe account”', investment_pressure: 'Investment pressure', otp_or_credential_request: 'Asks for OTP / PIN', threat_of_arrest_or_harm: 'Threatens arrest' };
const SIGNAL_ICONS = { authority_impersonation: 'user', secrecy: 'lock', urgency: 'clock', remote_app_install: 'tool', safe_account: 'database', investment_pressure: 'sparkles', otp_or_credential_request: 'lock', threat_of_arrest_or_harm: 'alert' };
const MARKER_TEXT = { authority: 'The caller claims to be an official.', threat: 'The caller is threatening you.', secrecy: 'The caller wants you to keep this secret.', remote_app: 'The caller wants you to install a screen-sharing app.', safe_account: 'The caller wants you to move money to a “safe” account.', urgency: 'The caller is rushing you.', otp: 'The caller is asking for an OTP or PIN.', payment_demand: 'The caller is asking you to pay now.' };
const FEEDBACK = {
  en: { hangup: 'Hanging up ends the scammer’s control. A real official never minds if you call back on the published number.', verify: 'Good instinct. Call the official number yourself, or your family. Never use a number the caller gives you.', comply: 'This is what the scammer wants. No officer, bank or company asks for money, an OTP or screen access on a call.', benignComply: 'This caller was genuine, but it is still wise to double-check a large payment.', benignHangup: 'Safe, but this caller was genuine. Asking to verify would have been enough.', benignVerify: 'Exactly right. Verifying first costs a minute and protects you either way.' },
  hi: { hangup: 'कॉल काटते ही ठग का नियंत्रण खत्म हो जाता है। असली अधिकारी को आपत्ति नहीं होती अगर आप आधिकारिक नंबर पर वापस कॉल करें।', verify: 'सही सोच। खुद आधिकारिक नंबर या परिवार को कॉल करें। कॉलर का दिया नंबर कभी न इस्तेमाल करें।', comply: 'ठग यही चाहता है। कोई अधिकारी, बैंक या कंपनी कॉल पर पैसा, OTP या स्क्रीन एक्सेस नहीं माँगती।', benignComply: 'यह कॉलर असली था, फिर भी बड़े भुगतान की दोबारा जाँच समझदारी है।', benignHangup: 'सुरक्षित, पर यह कॉलर असली था। जाँच के लिए कहना काफ़ी होता।', benignVerify: 'बिल्कुल सही। पहले जाँच में एक मिनट लगता है और हर हाल में बचाव होता है।' },
  hinglish: { hangup: 'Call kaatte hi scammer ka control khatam. Asli officer ko koi aitraaz nahi hota agar aap official number par wapas call karein.', verify: 'Sahi soch. Khud official number ya family ko call karein. Caller ka diya number kabhi use na karein.', comply: 'Scammer yahi chahta hai. Koi officer, bank ya company call par paisa, OTP ya screen access nahi maangti.', benignComply: 'Yeh caller asli tha, phir bhi bade payment ko dobara check karna samajhdari hai.', benignHangup: 'Safe, par yeh caller asli tha. Verify karne ke liye kehna kaafi hota.', benignVerify: 'Bilkul sahi. Pehle verify karne mein ek minute lagta hai aur har haal mein bachav hota hai.' },
};
function lang() { const l = (S.profile && S.profile.language) || 'en'; return T[l] ? l : 'en'; }
function t(k) { return (T[lang()] && T[lang()][k]) || T.en[k]; }
function fb(k) { const f = FEEDBACK[lang()] || FEEDBACK.en; return f[k] || FEEDBACK.en[k]; }

// ---------- tiny UI helpers ----------
function show(view) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('is-active'));
  const el = $('view-' + view); el.classList.add('is-active');
  const h = el.querySelector('h1, .hero__title'); if (h) { h.setAttribute('tabindex', '-1'); h.focus({ preventScroll: true }); }
  const body = el.querySelector('.view__body'); if (body) body.scrollTop = 0;
}
function log(msg) { const el = $('log'); if (!el) return; el.textContent = `[${new Date().toLocaleTimeString()}] ${msg}\n` + el.textContent.slice(0, 6000); }
function toast(msg, ms = 2800) { const el = $('toast'); el.textContent = msg; el.classList.add('is-open'); clearTimeout(el._h); el._h = setTimeout(() => el.classList.remove('is-open'), ms); }
function openSheet(id) { const s = $(id); s.classList.add('is-open'); s._prev = document.activeElement; const f = s.querySelector('input:not([type=radio]), select, button'); if (f) setTimeout(() => f.focus(), 50); }
function closeSheet(id) { const s = $(id); s.classList.remove('is-open'); if (s._prev && s._prev.focus) s._prev.focus(); }
function setIcon(id, name) { const el = $(id); if (el) el.innerHTML = icon(name); }
function fmtIndian(n) { return Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 }); }
function parseAmount(s) { const v = String(s || '').replace(/[^\d.]/g, ''); return v ? Number(v) : 0; }
function amountWords(n) { if (!n) return ''; if (n >= 1e7) return `${+(n / 1e7).toFixed(2)} crore rupees`; if (n >= 1e5) return `${+(n / 1e5).toFixed(2)} lakh rupees`; if (n >= 1e3) return `${+(n / 1e3).toFixed(1)} thousand rupees`; return `${n} rupees`; }
function setInvalid(fieldId, bad) { $(fieldId).classList.toggle('is-invalid', !!bad); const inp = $(fieldId).querySelector('input'); if (inp) inp.setAttribute('aria-invalid', bad ? 'true' : 'false'); }
setInterval(() => { $('clock').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }, 1000);

const ICON_SLOTS = { gCardIco: 'shield', icoPay: 'pay', icoIncoming: 'phone', icoDrill: 'graduation', icoDesk: 'list', callerAvatar: 'user', whisperIco: 'ear', audioIco: 'volumeX', trEmptyIco: 'message', micIco: 'micOff', icoMic: 'mic', icoReplay: 'play', icoOpenPay: 'pay', icoEnd: 'phoneOff', icoBack: 'arrowLeft', payCallIco: 'phone', icoSend: 'pay', holdIco: 'shield', icoVoice: 'volume', evCallIco: 'phone', evPayeeIco: 'database', alertIco: 'bell', talkIco: 'speak', talkErrIco: 'warn', icoCancel: 'xCircle', icoTalk: 'speak', doneIco: 'checkCircle', icoDrillBack: 'arrowLeft', drillInfoIco: 'info', icoDrillStart: 'play', drillQIco: 'question', drillFbIco: 'info', drillSumIco: 'graduation', obIco1: 'ear', obIco2: 'hand', obIco3: 'users', confirmIco: 'alert', brandIco: 'shield', gLangIcon: 'speak', gContactIcon: 'users' };
Object.entries(ICON_SLOTS).forEach(([id, n]) => setIcon(id, n));

// ---------- init / session ----------
async function init() {
  S.userId = qs('user') || 'demo-user';
  $('userSel').value = S.userId;
  try {
    const snap = await api('/api/sessions', 'POST', { session_id: qs('session') || null, user_id: S.userId, mode: 'audio' });
    S.sid = snap.session_id; S.profile = snap.profile;
    S.scripts = await api('/api/scripts');
  } catch (e) { renderBootError(e); return; }
  $('sidText').textContent = S.sid;
  const link = `/scammer?session=${S.sid}`; $('scammerLink').href = link; $('scammerLink2').href = link; if ($('callerLink')) $('callerLink').href = `/call?session=${S.sid}`; if ($('familyLink')) $('familyLink').href = `/family?user=${S.userId}`;
  $('homeName').textContent = `Namaste, ${S.profile.name}`;
  const opts = S.scripts.map(s => `<option value="${s.id}">${esc(s.title)} (${s.language})</option>`).join('');
  $('scriptSel').innerHTML = opts; $('drillScriptSel').innerHTML = opts;
  renderGuardianCard(); setListening(false);
  connectEvents();
  log(`session ${S.sid} ready for ${S.profile.name}`); clog('page_loaded', navigator.userAgent.slice(0, 80));
  show('home');
  if (!localStorage.getItem(ONBOARD_KEY())) startOnboarding();
}
function renderBootError(e) {
  $('bootBody').innerHTML = `<div class="empty" style="margin-top:40px">${icon('wifiOff')}<div class="empty__title">Cannot reach Rakshak</div><div class="small">${esc(e.network ? 'The server did not answer. Check the connection and try again.' : e.message)}</div><button class="btn btn--primary" id="btnRetry" type="button" style="margin-top:16px">Try again</button></div>`;
  $('btnRetry').onclick = () => { $('bootBody').innerHTML = '<p class="muted small" style="text-align:center;margin-top:40px"><span class="spinner"></span> Connecting…</p>'; init(); };
  show('boot');
}
function connectEvents() {
  const gen = ++S.evGen;
  S.evWS = openWS(`/ws/events/${S.sid}?role=user`, { onJson: onEvent, onClose: () => { if (gen === S.evGen) setTimeout(() => { if (gen === S.evGen) connectEvents(); }, 1500); } });
}
async function newSession() {
  const snap = await api('/api/sessions', 'POST', { session_id: null, user_id: S.userId, mode: 'audio' });
  S.sid = snap.session_id; S.lastRubric = null; S.replayPayment = null; S.case = null;
  if (S.callWS) { try { S.callWS.close(); } catch (e) {} S.callWS = null; }
  S.evGen++; if (S.evWS) { try { S.evWS.close(); } catch (e) {} }
  $('sidText').textContent = S.sid; const link = `/scammer?session=${S.sid}`; $('scammerLink').href = link; $('scammerLink2').href = link; if ($('callerLink')) $('callerLink').href = `/call?session=${S.sid}`; if ($('familyLink')) $('familyLink').href = `/family?user=${S.userId}`;
  resetCallUI(); connectEvents(); log(`new session ${S.sid}`);
}

// ---------- events ----------
function onEvent(ev) {
  switch (ev.type) {
    case 'hello': if (ev.snapshot) { ev.snapshot.turns.forEach(addTranscript); if (ev.snapshot.rubric) renderRubric(ev.snapshot.rubric); if (ev.snapshot.state === 'active') setListening(true); if (ev.snapshot.live_call && !ev.snapshot.call_accepted) onIncoming({ caller_display: ev.snapshot.caller_display }); } break;
    case 'transcript': addTranscript(ev.turn); break;
    case 'risk_update': renderRubric(ev.rubric); log(`risk ${Math.round(ev.rubric.risk_score * 100)}% stage=${ev.rubric.stage} (${ev.rubric.latency_ms} ms)`); break;
    case 'whisper': $('whisperText').textContent = ev.text; $('whisperBanner').hidden = false; addTranscript({ speaker: 'rakshak', text: ev.text }); log('whisper: ' + ev.text); break;
    case 'agent_running': setPayStatus('Rakshak is checking the payee and the call…'); break;
    case 'decision': onDecision(ev); break;
    case 'case_update': if (S.case && ev.case.case_id === S.case.case_id) { S.case = ev.case; if ($('view-hold').classList.contains('is-active') && ev.agent) { renderHold(ev.case, null); toast('Rakshak’s investigator confirmed the decision'); } } break;
    case 'replay_started': if (D.active) { $('drillStagePill').textContent = 'playing'; } break;
    case 'replay_paused': case 'replay_finished':
      S.replayPayment = ev.payment_attempt; log('replay reached payment demand');
      if (D.active) { if (ev.type === 'replay_finished') drillFinish(); break; }
      if (S.replayPayment) { if ($('view-pay').classList.contains('is-active') && !$('vpaInp').value) { fillPayment(S.replayPayment); toast('Payee filled in from the call'); } else { toast('The caller is demanding payment: tap “Open UPI pay”'); } }
      break;
    case 'replay_stopped': if (D.active) drillFinish(true); break;
    case 'replay_marker': log('script marker: ' + ev.marker); if (D.active) drillMarker(ev.marker, ev.n); break;
    case 'party_joined': log('party joined: ' + ev.role); break;
    case 'incoming_call': onIncoming(ev); break;
    case 'call_accepted': break;
    case 'party_muted': if (ev.role === 'caller') toast(ev.muted ? 'Caller muted' : 'Caller unmuted', 1200); break;
    case 'call_started': setListening(true); break;
    case 'call_ended': stopCallUI(); setListening(false); break;
    case 'analysis_error': log('analysis error: ' + ev.error); toast('Analysis hiccup, Rakshak keeps listening'); break;
  }
}
function addTranscript(turn) {
  const targets = [$('transcript')]; if (D.active) targets.push($('drillTranscript'));
  for (const el of targets) {
    const empty = el.querySelector('.empty'); if (empty) empty.remove();
    const who = turn.speaker === 'caller' ? 'Caller' : turn.speaker === 'user' ? 'You' : 'Rakshak';
    const d = document.createElement('div'); d.className = 'tr__turn tr__turn--' + (turn.speaker === 'caller' ? 'caller' : turn.speaker === 'user' ? 'user' : 'rakshak');
    d.innerHTML = `<span class="tr__who">${who}</span><span class="tr__text">${esc(turn.text)}</span>`; el.appendChild(d); el.scrollTop = el.scrollHeight;
  }
}
function setGauge(r) {
  const pct = Math.round((r || 0) * 100), band = riskBand(r || 0), C = 289.03;
  $('riskArc').style.strokeDashoffset = String(C * (1 - pct / 100));
  $('riskPct').textContent = pct + '%';
  const g = $('riskGauge'); g.className = 'gauge gauge--' + band;
  const label = { low: 'Low', elevated: 'Elevated', high: 'High' }[band];
  $('riskBandLabel').textContent = label; $('riskBandIco').innerHTML = icon({ low: 'checkCircle', elevated: 'warn', high: 'alert' }[band]);
  $('riskLive').textContent = `Scam risk ${pct} percent, ${label.toLowerCase()}`;
  if (D.active) { $('drillMeter').className = 'meter meter--' + band; $('drillMeter').setAttribute('aria-valuenow', pct); $('drillMeterFill').style.width = pct + '%'; $('drillRiskText').textContent = `${pct}% · ${label.toLowerCase()}`; }
}
function chipsFor(signals, ok = 'no coercion signals') {
  const on = Object.entries(signals || {}).filter(([, v]) => v);
  if (!on.length) return `<span class="chip chip--ok">${icon('check')}${ok}</span>`;
  return on.map(([k]) => `<span class="chip">${icon(SIGNAL_ICONS[k] || 'alert')}${SIGNAL_LABELS[k] || k.replace(/_/g, ' ')}</span>`).join('');
}
function renderRubric(r) {
  S.lastRubric = r; if (D.active) D.lastRubric = r;
  setGauge(r.risk_score);
  $('stagePill').textContent = (r.stage || '').replace(/_/g, ' ') || 'listening'; $('stagePill').className = 'pill ' + (riskBand(r.risk_score) === 'high' ? 'pill--hold' : riskBand(r.risk_score) === 'elevated' ? 'pill--warn' : 'pill--ok');
  $('signalChips').innerHTML = chipsFor(r.signals, 'nothing suspicious yet');
  const reasons = (r.reasons_user_language && r.reasons_user_language.length ? r.reasons_user_language : r.reasons) || [];
  $('reasons').innerHTML = reasons.slice(0, 4).map(x => `<li>${esc(x)}</li>`).join('');
  $('riskHint').textContent = r.scam_type && r.scam_type !== 'none' ? `Looks like a ${r.scam_type.replace(/_/g, ' ')} scam` : 'Rakshak listens for pressure, threats and secrecy.';
}

// ---------- guardian card / listening indicator ----------
function tier() { const v = S.profile && S.profile.privacy_tier; return v === 0 || v === 1 || v === 2 ? v : 2; }
function renderGuardianCard() {
  const p = S.profile, on = !!p.guardian_enabled;
  $('gStatusIcon').innerHTML = icon(on ? 'shield' : 'shieldOff'); $('gStatusText').textContent = on ? 'Guardian mode is on' : 'Guardian mode is off';
  $('gTierText').textContent = on ? TIER_TEXT[tier()] : 'Rakshak will not listen to calls. The payee check still runs when you pay.';
  $('gContactText').textContent = p.trusted_contact_name || 'None set'; $('gLangText').textContent = LANG_NAMES[p.language] || p.language;
  $('guardianPill').className = 'pill ' + (on ? 'pill--ok' : 'pill--outline'); $('guardianPill').textContent = on ? 'Guardian on' : 'Guardian off';
}
function setListening(active) {
  S.callActive = active; const on = active && S.profile && S.profile.guardian_enabled;
  const chip = $('listenChip'); chip.classList.toggle('is-off', !on);
  $('listenText').textContent = on ? (LISTEN_TEXT[tier()] || t('listening')) : (active ? 'Guardian off' : 'Rakshak idle');
}

// ---------- onboarding ----------
let obStep = 1;
function startOnboarding(step = 1) {
  const p = S.profile; $('obContact').value = p.trusted_contact_name || ''; $('obLang').value = p.language || 'hi'; $('obGuardian').checked = !!p.guardian_enabled;
  const tr = document.querySelector(`input[name=tier][value="${tier()}"]`); if (tr) tr.checked = true;
  obStep = step; renderObStep(); openSheet('onboardSheet');
}
function renderObStep() {
  document.querySelectorAll('.onboard-step').forEach(s => s.classList.toggle('is-active', Number(s.dataset.step) === obStep));
  [...$('obStepper').children].forEach((el, i) => el.classList.toggle('is-done', i < obStep));
  $('obBack').textContent = obStep === 1 ? 'Skip' : 'Back'; $('obNext').textContent = obStep === 3 ? 'Save & finish' : 'Next';
  $('obStepLive').textContent = `Step ${obStep} of 3`;
  const panel = document.querySelector('#onboardSheet .sheet__panel'); panel.scrollTop = 0;
  const f = panel.querySelector('.onboard-step.is-active input, .onboard-step.is-active select'); if (f) f.focus();
}
async function finishOnboarding() {
  const tierVal = Number((document.querySelector('input[name=tier]:checked') || {}).value ?? 2);
  try {
    S.profile = await api(`/api/profiles/${S.userId}`, 'PUT', { language: $('obLang').value, trusted_contact_name: $('obContact').value.trim(), guardian_enabled: $('obGuardian').checked, privacy_tier: tierVal });
  } catch (e) { toast('Could not save: ' + e.message); return; }
  localStorage.setItem(ONBOARD_KEY(), '1'); renderGuardianCard(); setListening(S.callActive); closeSheet('onboardSheet'); toast('Guardian settings saved');
}
$('obNext').onclick = () => { if (obStep < 3) { obStep++; renderObStep(); } else finishOnboarding(); };
$('obBack').onclick = () => { if (obStep === 1) { localStorage.setItem(ONBOARD_KEY(), '1'); closeSheet('onboardSheet'); } else { obStep--; renderObStep(); } };
$('btnEditGuardian').onclick = () => startOnboarding(2);
$('btnReOnboard').onclick = () => { localStorage.removeItem(ONBOARD_KEY()); startOnboarding(1); };

// ---------- call ----------
let _ring = null;
function ringStart() {
  try {
    const ctx = S.caller.ensure();
    const beep = () => { const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.value = 440; o.connect(g); g.connect(ctx.destination); const t = ctx.currentTime; g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.25, t + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.9); o.start(t); o.stop(t + 1); };
    beep(); _ring = setInterval(beep, 2000);
  } catch (e) { /* audio locked until first tap: the sheet and vibration still show */ }
  if (navigator.vibrate) navigator.vibrate([400, 200, 400, 200, 400]);
}
function ringStop() { if (_ring) { clearInterval(_ring); _ring = null; } if (navigator.vibrate) navigator.vibrate(0); }
function clog(event, detail) { if (!S.sid) return; fetch(`/api/sessions/${S.sid}/clientlog`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event, detail: detail ? String(detail).slice(0, 200) : null, role: 'user' }) }).catch(() => {}); }
function onIncoming(ev) {
  if ($('view-call').classList.contains('is-active')) {  // already on the call screen: connect the caller straight away
    if (S.callWS && S.callWS.readyState === 1) { S.callWS.send(JSON.stringify({ type: 'accept' })); } else { S.pendingAccept = true; connectCallWS(); }
    if (!S.mic) toggleMic();
    toast('Caller connected to this call'); clog('ring_autoaccepted'); return;
  }
  clog('ring_shown', ev.caller_display);
  S.callerDisplay = ev.caller_display || 'Unknown number';
  $('incTitle').textContent = S.callerDisplay; openSheet('incomingSheet'); ringStart(); log('incoming call from ' + S.callerDisplay);
}
async function acceptCall() {
  ringStop(); closeSheet('incomingSheet'); S.pendingAccept = true; clog('answer_tapped');
  await startCall();
  if (S.callWS && S.callWS.readyState === 1 && S.pendingAccept) { S.pendingAccept = false; S.callWS.send(JSON.stringify({ type: 'accept' })); }
  if (!S.mic) await toggleMic();
}
async function declineCall() {
  ringStop(); closeSheet('incomingSheet');
  if (S.callWS && S.callWS.readyState === 1) { try { S.callWS.send(JSON.stringify({ type: 'decline' })); } catch (e) {} }
  else { try { await api(`/api/sessions/${S.sid}/end`); } catch (e) {} }
  toast('Call declined');
}
async function startCall() {
  show('call'); $('callerNum').textContent = S.callerDisplay || '+91 98765 00301'; S.callActive = true;
  resetCallUI();
  S.callStart = Date.now(); clearInterval(S.timer);
  S.timer = setInterval(() => { $('callTimer').textContent = fmtClock((Date.now() - S.callStart) / 1000); }, 1000);
  S.caller.ensure(); S.guardian.ensure();
  S.caller.onState = updateAudioBanner; setTimeout(updateAudioBanner, 400);
  connectCallWS(); setListening(true);
  if (tier() === 0 && S.profile.guardian_enabled) toast('Tier 0: Rakshak will not hear this call. The payee check still runs when you pay.', 4500);
}
function resetCallUI() {
  $('whisperBanner').hidden = true; $('micBanner').hidden = true; $('audioBanner').hidden = true;
  $('transcript').innerHTML = `<div class="empty">${icon('message')}<div class="empty__title">Waiting for speech</div><div class="small">Turn on your mic or play a scripted caller.</div></div>`;
  setGauge(0); $('signalChips').innerHTML = ''; $('reasons').innerHTML = ''; $('stagePill').textContent = 'waiting'; $('stagePill').className = 'pill'; $('riskHint').textContent = 'Rakshak listens for pressure, threats and secrecy.';
}
function updateAudioBanner() { $('audioBanner').hidden = !(S.caller.blocked() && $('view-call').classList.contains('is-active')); }
function connectCallWS() {
  if (S.callWS && S.callWS.readyState === 1) return;
  S.callWS = openWS(`/ws/call/${S.sid}/user`, {
    onBinary: (buf) => S.caller.play(new Int16Array(buf), 16000),
    onJson: (m) => {
      if (m.type === 'rakshak_audio' && m.audio_b64) { const pcm = b64ToInt16(m.audio_b64); if (m.kind !== 'whisper') S.holdAudio = { pcm, rate: m.rate || 16000 }; S.caller.duck(0.15, 8); S.guardian.play(pcm, m.rate || 16000); }
      if (m.type === 'caller_audio' && m.audio_b64) { S.caller.play(b64ToInt16(m.audio_b64), m.rate || 16000); }
    },
    onOpen: () => { log('call audio channel open'); if (S.pendingAccept) { S.pendingAccept = false; S.callWS.send(JSON.stringify({ type: 'accept' })); } },
  });
}
function setMicUI(on) { $('btnMic').setAttribute('aria-pressed', on ? 'true' : 'false'); $('btnMic').innerHTML = icon(on ? 'micOff' : 'mic') + (on ? 'Stop my mic' : 'Use my mic'); $('btnMic').classList.toggle('btn--primary', on); $('btnMic').classList.toggle('btn--secondary', !on); }
async function toggleMic() {
  if (S.mic) { S.mic.stop(); S.mic = null; setMicUI(false); return; }
  try {
    S.mic = new Mic((int16) => { if (S.callWS && S.callWS.readyState === 1) S.callWS.send(int16.buffer); });
    await S.mic.start(); setMicUI(true); $('micBanner').hidden = true; log('microphone streaming (16 kHz)'); clog('mic_ok');
  } catch (e) {
    S.mic = null; setMicUI(false); clog('mic_error', e.kind || e.message);
    const title = e.kind === 'denied' ? 'Microphone permission was denied' : e.kind === 'nodevice' ? 'No microphone found' : 'Microphone not available';
    const text = e.kind === 'denied' ? 'Rakshak needs the mic only to hear the caller through this phone. Allow the microphone in your browser’s site settings, or run the demo with a scripted caller.' : e.kind === 'unsupported' ? 'This browser cannot capture audio. Use Chrome or Safari, or run the demo with a scripted caller.' : e.message;
    $('micBannerTitle').textContent = title; $('micBannerText').textContent = text; $('micBanner').hidden = false; log('mic error: ' + e.message);
  }
}
function stopCallUI() { clearInterval(S.timer); if (S.mic) { S.mic.stop(); S.mic = null; } setMicUI(false); S.callActive = false; ringStop(); if ($('incomingSheet').classList.contains('is-open')) closeSheet('incomingSheet'); }
async function endCall() { try { await api(`/api/sessions/${S.sid}/end`); } catch (e) {} stopCallUI(); setListening(false); show('home'); }

// ---------- payment ----------
function fillPayment(p) { $('vpaInp').value = p.vpa; $('payeeNameInp').value = p.payee_name || ''; $('amountInp').value = fmtIndian(p.amount_inr); updateAmountPreview(); }
function openPay() {
  show('pay');
  const p = S.replayPayment; if (p) fillPayment(p);
  if (S.callActive) { $('payCallNote').hidden = false; $('payCallText').textContent = S.lastRubric ? `Current scam risk ${Math.round(S.lastRubric.risk_score * 100)}% (${riskBand(S.lastRubric.risk_score)}). Rakshak will check this payment before it goes.` : 'Rakshak will check this payment before it goes.'; } else { $('payCallNote').hidden = true; }
  $('payStatus').hidden = true; setInvalid('fVpa', false); setInvalid('fAmt', false);
  updateAmountPreview(); prewarmAmount();
}
function setPayStatus(text) { $('payStatus').hidden = !text; $('payStatusText').textContent = text || ''; }
let _pwLast = null;
function prewarmAmount() { const a = parseAmount($('amountInp').value); if (!a || a === _pwLast) return; _pwLast = a; fetch(`/api/sessions/${S.sid}/prewarm?amount_inr=${a}`, { method: 'POST' }).catch(() => {}); }
function updateAmountPreview() { const a = parseAmount($('amountInp').value); $('amountPreview').textContent = a ? `${fmtINR(a)} · ${amountWords(a)}` : ''; }
function validatePay() {
  const vpa = $('vpaInp').value.trim(), amount = parseAmount($('amountInp').value);
  const vpaOk = /^[\w.\-]{2,}@[a-z][a-z0-9.\-]{1,}$/i.test(vpa), amtOk = amount > 0;
  setInvalid('fVpa', !vpaOk); setInvalid('fAmt', !amtOk);
  if (!vpaOk) { $('vpaInp').focus(); return null; } if (!amtOk) { $('amountInp').focus(); return null; }
  return { vpa, amount };
}
async function sendPayment() {
  const v = validatePay(); if (!v) return;
  const name = $('payeeNameInp').value.trim();
  $('btnSend').disabled = true; setPayStatus('Checking with Rakshak…');
  S.guardian.ensure();
  try {
    const res = await api('/api/payments', 'POST', { session_id: S.sid, vpa: v.vpa, payee_name: name, amount_inr: v.amount });
    if (!S.case || S.case.case_id !== res.case.case_id) onDecision({ case: res.case, audio_b64: res.audio_b64, spoken_text: res.spoken_text, audio_rate: 16000 });
    else if (res.audio_b64 && !S.holdAudio) { S.holdAudio = { pcm: b64ToInt16(res.audio_b64), rate: 16000 }; }
  } catch (e) { toast(e.network ? 'Cannot reach Rakshak. The payment was not sent.' : 'Payment check failed: ' + e.message); log(e.message); }
  $('btnSend').disabled = false; setPayStatus('');
}
function onDecision(ev) {
  const c = ev.case; S.case = c; const d = c.decision;
  log(`decision ${d.action} (${d.decided_by}, conf ${d.confidence}) in ${d.latency_ms || '-'} ms`);
  if (ev.audio_b64) { const pcm = b64ToInt16(ev.audio_b64); S.holdAudio = { pcm, rate: ev.audio_rate || 16000 }; S.caller.duck(0.1, 20); S.guardian.play(pcm, ev.audio_rate || 16000); }
  if (d.action === 'proceed') {
    showDone('proceed', t('sentTitle'), `${fmtINR(c.payment.amount_inr)} to ${c.payment.vpa}`, `<div class="status-tile">${icon('checkCircle')}<div>Rakshak saw no coercion on the call and the payee looks ordinary (score ${c.policy.score}).</div></div>`);
    $('decisionLive').textContent = `Payment of ${fmtINR(c.payment.amount_inr)} sent.`; return;
  }
  show('hold'); renderHold(c, ev.spoken_text);
}
function renderHold(c, spoken) {
  const d = c.decision, warn = d.action === 'warn', p = c.payee || {};
  $('holdHead').className = 'hero ' + (warn ? 'hero--warn' : 'hero--hold'); $('holdIco').innerHTML = icon(warn ? 'warn' : 'hand');
  $('holdTitle').textContent = warn ? t('warnTitle') : t('holdTitle');
  $('holdSub').textContent = `${fmtINR(c.payment.amount_inr)} to ${c.payment.vpa}${c.payment.payee_name ? ' (' + c.payment.payee_name + ')' : ''}`;
  if (spoken) $('spokenText').textContent = spoken; else if (!$('spokenText').textContent.trim()) $('spokenText').textContent = d.user_message || '';
  $('decisionLive').textContent = `${warn ? 'Warning' : 'Payment paused'}. ${spoken || d.user_message || ''}`;
  // the call
  $('holdChips').innerHTML = chipsFor((c.rubric || {}).signals);
  const ul = (c.rubric && c.rubric.reasons_user_language) || [];
  const reasons = [...(lang() === 'en' ? [] : ul), ...(d.reasons || [])].filter((x, i, a) => a.indexOf(x) === i).slice(0, 5);
  $('holdReasons').innerHTML = reasons.map(r => `<li>${esc(r)}</li>`).join('') || '<li class="muted">No call signals, the payee itself is the concern.</li>';
  // the payee
  const band = p.risk_band || 'unknown', bad = band === 'critical' || band === 'high', mid = band === 'medium';
  $('payeeBand').className = 'pill ' + (bad ? 'pill--hold' : mid ? 'pill--warn' : 'pill--ok'); $('payeeBand').innerHTML = `${icon(bad ? 'alert' : mid ? 'warn' : 'check')}${band} risk`;
  $('payeeVpa').textContent = `${p.vpa || c.payment.vpa}${p.display_name ? ' · ' + p.display_name : ''}`;
  const pct = (v) => v == null ? '–' : Math.round(v * 100) + '%';
  const days = (v) => v == null ? '–' : v + (v === 1 ? ' day' : ' days');
  const rows = [
    ['Risk band', band, bad ? 'is-bad' : mid ? 'is-warn' : 'is-ok'],
    ['Mule score', p.mule_risk_score == null ? '–' : p.mule_risk_score, (p.mule_risk_score || 0) >= 0.7 ? 'is-bad' : ''],
    ['Payers in last 48 h', p.fan_in_48h ?? '–', (p.fan_in_48h || 0) >= 5 ? 'is-bad' : ''],
    ['Cash-out ratio (7 d)', pct(p.cash_out_ratio_7d), (p.cash_out_ratio_7d || 0) >= 0.8 ? 'is-bad' : ''],
    ['Dormant before burst', days(p.dormant_days_before_burst), ''],
    ['Telecom risk (FRI)', (p.fri_level || '–').replace(/_/g, ' '), /high/.test(p.fri_level || '') ? 'is-bad' : ''],
    ['1930 complaints', p.linked_complaints_1930 ?? 0, (p.linked_complaints_1930 || 0) > 0 ? 'is-bad' : 'is-ok'],
    ['Account age', days(p.account_age_days), (p.account_age_days != null && p.account_age_days < 30) ? 'is-warn' : ''],
  ];
  $('payeeCard').innerHTML = rows.map(([k, v, cls]) => `<dt>${k}</dt><dd class="${cls}">${esc(v)}</dd>`).join('');
  $('payeeLineage').innerHTML = `${icon('database')} ${esc(lineageText(p))}`; $('payeeLineage').style.display = 'flex'; $('payeeLineage').style.gap = '6px'; $('payeeLineage').style.alignItems = 'center';
  // trusted contact
  if (c.alert) { $('alertLine').hidden = false; $('alertText').innerHTML = `<b>${esc(c.alert.contact_name)}</b> has been told (${c.alert.channels.map(x => x.replace('_', '-')).join(', ')}). Ask them before you do anything else.`; }
  else if (d.notify_trusted_contact) { $('alertLine').hidden = false; $('alertText').innerHTML = `<span class="spinner"></span> Telling ${esc(S.profile.trusted_contact_name || 'your trusted contact')}…`; }
  else { $('alertLine').hidden = true; }
  $('btnOverride').textContent = warn ? 'Continue payment anyway' : 'I know this person — pay anyway';
  $('btnCancelPay').innerHTML = icon('xCircle') + (warn ? 'Cancel payment' : 'Cancel payment & report');
  $('talkBox').hidden = true;
  clearInterval(S.countdownT);
  if (!warn) {
    const end = (c.hold_until || (Date.now() / 1000 + 1800)) * 1000;
    const tick = () => { const s = Math.max(0, Math.floor((end - Date.now()) / 1000)); $('countdown').firstChild.textContent = fmtClock(s); };
    $('countdown').firstChild.textContent = '30:00'; tick(); S.countdownT = setInterval(tick, 1000); $('countdownLbl').textContent = 'until this hold expires'; $('countdown').style.display = '';
  } else { $('countdown').style.display = 'none'; }
}
function lineageText(p) {
  const L = p.lineage;
  if (L) {
    if (typeof L === 'string') return L;
    const n = L.n_transactions ?? L.transactions ?? L.rows ?? L.n;
    const at = L.refreshed_at ?? L.refreshed ?? L.updated_at;
    const when = typeof at === 'number' ? relTime(at > 1e12 ? at / 1000 : at) : (at ? String(at) : 'recently');
    return `features computed from ${n != null ? fmtIndian(n) : 'N'} transactions, refreshed ${when}`;
  }
  if (p.source === 'bigquery') return 'features from the BigQuery payee risk table';
  if (p.source === 'unknown') return 'no history for this payee (thin file): demo risk table';
  return 'demo risk table (data/payees.json)';
}
async function replayVoice() {
  S.guardian.ensure();
  if (S.holdAudio) { S.guardian.play(S.holdAudio.pcm, S.holdAudio.rate); return; }
  const text = $('spokenText').textContent.trim(); if (!text) return;
  $('btnReplayVoice').disabled = true;
  try { const r = await api('/api/tts?text=' + encodeURIComponent(text)); if (r.audio_b64 && r.bytes) { S.holdAudio = { pcm: b64ToInt16(r.audio_b64), rate: r.rate || 16000 }; S.guardian.play(S.holdAudio.pcm, S.holdAudio.rate); } else toast('Voice is not available offline; the message is shown above.'); }
  catch (e) { toast('Voice is not available right now'); }
  $('btnReplayVoice').disabled = false;
}
function showDone(kind, title, sub, bodyHtml) {
  $('doneHead').className = 'hero ' + (kind === 'cancel' ? 'hero--proceed' : kind === 'override' ? 'hero--warn' : 'hero--proceed');
  $('doneIco').innerHTML = icon(kind === 'cancel' ? 'shield' : kind === 'override' ? 'warn' : 'checkCircle');
  $('doneTitle').textContent = title; $('doneSub').textContent = sub || ''; $('doneBody').innerHTML = bodyHtml; show('done');
}
async function cancelPayment() {
  if (!S.case) return; $('btnCancelPay').disabled = true;
  try { await api(`/api/cases/${S.case.case_id}/cancel`, 'POST'); } catch (e) { toast('Could not reach the server: ' + e.message); $('btnCancelPay').disabled = false; return; }
  $('btnCancelPay').disabled = false; clearInterval(S.countdownT); endTalk();
  showDone('cancel', t('cancelledTitle'), 'Nothing was sent', `<div class="stack-sm"><div class="status-tile">${icon('checkCircle')}<div>The bank’s fraud desk has case <b class="mono">${S.case.case_id}</b> and the payee is being reported.</div></div><div class="status-tile">${icon('phoneOff')}<div>You can hang up now. No officer ever asks for money on a call.</div></div></div>`);
}
function askOverride() {
  if (!S.case) return;
  if (S.case.decision.action === 'warn') return doOverride('customer continued after warning');
  $('confirmText').textContent = `You are about to send ${fmtINR(S.case.payment.amount_inr)} to ${S.case.payment.vpa}. ${S.case.alert ? S.case.alert.contact_name + ' has been told.' : ''}`;
  $('confirmAmount').value = ''; setInvalid('fConfirm', false); openSheet('confirmSheet');
}
async function doOverride(reason) {
  const c = S.case; try { await api(`/api/cases/${c.case_id}/override`, 'POST', { reason }); } catch (e) { toast('Could not reach the server: ' + e.message); return; }
  clearInterval(S.countdownT); closeSheet('confirmSheet'); endTalk();
  showDone('override', 'Payment sent after your confirmation', `${fmtINR(c.payment.amount_inr)} to ${c.payment.vpa}`, `<div class="status-tile">${icon('info')}<div>The override is recorded on case <b class="mono">${c.case_id}</b>; the fraud desk will still review the payee.</div></div>`);
}

// ---------- post-hold voice conversation (Gemini Live) ----------
function talkError(msg) { $('talkError').hidden = false; $('talkErrorText').innerHTML = msg; $('talkPill').className = 'pill pill--outline'; $('talkPill').textContent = 'offline'; }
async function startTalk() {
  if (!S.case) return;
  $('talkBox').hidden = false; $('talkError').hidden = true; $('talkPill').className = 'pill pill--live'; $('talkPill').innerHTML = '<span class="dot"></span>connecting';
  $('talkLog').innerHTML = `<div class="tr__turn tr__turn--system"><span class="tr__who">Info</span><span class="tr__text">Connecting to Rakshak… speak after the tone.</span></div>`;
  $('talkBox').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  S.guardianPlayer.ensure(); S.talkReady = false;
  S.guardianWS = openWS(`/ws/guardian/${S.case.case_id}`, {
    onBinary: (buf) => S.guardianPlayer.play(new Int16Array(buf), 24000),
    onJson: (m) => {
      if (m.type === 'guardian_ready') { S.talkReady = true; $('talkLog').innerHTML = ''; $('talkPill').innerHTML = '<span class="dot"></span>live'; startGuardianMic(); }
      if (m.type === 'guardian_text') appendTalk('Rakshak', m.text);
      if (m.type === 'user_text') appendTalk('You', m.text);
      if (m.type === 'interrupted') S.guardianPlayer.flush();
      if (m.type === 'tool') { log('guardian tool: ' + m.name); if (m.name === 'request_release') askOverride(); if (m.name === 'call_trusted_contact') toast('Calling ' + (S.profile.trusted_contact_name || 'trusted contact') + '…'); if (m.name === 'keep_hold') toast('Hold kept. You are safe.'); }
      if (m.type === 'error') talkError(`Rakshak’s live voice is unavailable right now (${esc(m.error)}). You can still cancel the payment, or call ${esc(S.profile.trusted_contact_name || 'someone you trust')}.`);
    },
    onClose: () => { if (S.guardianMic) { S.guardianMic.stop(); S.guardianMic = null; } if (!S.talkReady && !$('talkBox').hidden && $('talkError').hidden) talkError(`Rakshak’s live voice is unavailable right now (the Live API is not configured on this server). You can still cancel the payment, or call ${esc(S.profile.trusted_contact_name || 'someone you trust')}.`); },
  });
}
let _talkLast = { who: null, el: null };
function appendTalk(who, text) {
  const el = $('talkLog');
  if (_talkLast.who === who && _talkLast.el) { _talkLast.el.querySelector('.tr__text').textContent += text; }
  else { const d = document.createElement('div'); d.className = 'tr__turn tr__turn--' + (who === 'You' ? 'user' : who === 'Rakshak' ? 'rakshak' : 'system'); d.innerHTML = `<span class="tr__who">${esc(who)}</span><span class="tr__text">${esc(text)}</span>`; el.appendChild(d); _talkLast = { who, el: d }; }
  el.scrollTop = el.scrollHeight;
}
async function startGuardianMic() { try { S.guardianMic = new Mic((int16) => { if (S.guardianWS && S.guardianWS.readyState === 1) S.guardianWS.send(int16.buffer); }); await S.guardianMic.start(); } catch (e) { appendTalk('Info', e.kind === 'denied' ? 'Microphone denied: Rakshak can speak but cannot hear you. Allow the mic in site settings.' : 'Mic unavailable: ' + e.message); } }
function endTalk() { if (S.guardianWS) { try { S.guardianWS.send(JSON.stringify({ type: 'end' })); S.guardianWS.close(); } catch (e) {} S.guardianWS = null; } if (S.guardianMic) { S.guardianMic.stop(); S.guardianMic = null; } $('talkBox').hidden = true; _talkLast = { who: null, el: null }; }

// ---------- practice drill ----------
async function drillStart() {
  const id = $('drillScriptSel').value; D.script = S.scripts.find(s => s.id === id) || null;
  D.active = true; D.queue = []; D.answers = []; D.lastRubric = null; D.benign = !!(D.script && (D.script.expected_outcome === 'proceed' || !D.script.scam_type));
  $('drillSetup').hidden = true; $('drillSummary').hidden = true; $('drillRun').hidden = false; $('drillChoice').hidden = true; $('drillTranscript').innerHTML = '';
  $('drillMeter').className = 'meter meter--low'; $('drillMeterFill').style.width = '0%'; $('drillRiskText').textContent = '0% · low'; $('drillStagePill').textContent = 'starting';
  S.caller.ensure(); S.guardian.ensure();
  if (S.lastRubric || S.case) { try { await newSession(); } catch (e) {} }  // a drill starts from a clean rubric
  connectCallWS(); setListening(true);
  try { await api(`/api/sessions/${S.sid}/replay`, 'POST', { script_id: id, voice: true, pace: 1.0, stop_at_marker: null }); log('drill: playing ' + id); }
  catch (e) { toast('Could not start the drill: ' + e.message); D.active = false; $('drillSetup').hidden = false; $('drillRun').hidden = true; }
}
function drillMarker(marker, n) {
  if (!MARKER_TEXT[marker]) return;
  D.queue.push({ marker, n }); if ($('drillChoice').hidden) drillShowNext();
}
function drillShowNext() {
  const item = D.queue.shift(); if (!item) { $('drillChoice').hidden = true; return; }
  D.pending = item;
  $('drillQ').innerHTML = icon('question') + t('drillQ'); $('drillMarkerText').textContent = MARKER_TEXT[item.marker];
  $('drillFeedback').hidden = true;
  const choices = [['hangup', 'phoneOff'], ['verify', 'checkCircle'], ['comply', 'hand']];
  $('drillChoices').innerHTML = choices.map(([k, ic]) => `<button class="btn btn--secondary btn--block" data-choice="${k}" type="button" style="justify-content:flex-start;text-align:left">${icon(ic)}<span><b>${esc(t(k))}</b><br><span class="small muted">${esc(t(k + 'D'))}</span></span></button>`).join('');
  $('drillChoices').querySelectorAll('button').forEach(b => b.onclick = () => drillAnswer(b.dataset.choice));
  $('drillChoice').hidden = false; $('drillChoice').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  const first = $('drillChoices').querySelector('button'); if (first) first.focus();
}
function drillAnswer(choice) {
  const item = D.pending; if (!item) return;
  const score = D.benign ? ({ verify: 2, comply: 1, hangup: 1 })[choice] : ({ hangup: 2, verify: 1, comply: 0 })[choice];
  const key = D.benign ? ('benign' + choice[0].toUpperCase() + choice.slice(1)) : choice;
  const grade = score === 2 ? 'good' : score === 1 ? 'ok' : 'bad';
  D.answers.push({ marker: item.marker, n: item.n, choice, score, grade });
  $('drillFeedback').className = 'banner ' + (grade === 'good' ? 'banner--ok' : grade === 'ok' ? 'banner--info' : 'banner--hold'); $('drillFeedback').hidden = false;
  $('drillFbIco').innerHTML = icon(grade === 'good' ? 'checkCircle' : grade === 'ok' ? 'info' : 'alert');
  $('drillFeedbackText').innerHTML = `<b>${esc(t(grade))}.</b> ${esc(fb(key))}`;
  $('drillChoices').querySelectorAll('button').forEach(b => { b.disabled = true; if (b.dataset.choice === choice) b.classList.add('btn--primary'); });
  setTimeout(() => { if (D.queue.length) drillShowNext(); }, 2500);
}
async function drillFinish(stopped) {
  if (!D.active) return; D.active = false;
  const r = D.lastRubric || S.lastRubric;
  const total = D.answers.length * 2, got = D.answers.reduce((a, x) => a + x.score, 0), ratio = total ? got / total : 0;
  $('drillRun').hidden = true; $('drillSummary').hidden = false;
  $('drillHero').className = 'hero ' + (ratio >= 0.75 ? 'hero--proceed' : ratio >= 0.4 ? 'hero--warn' : 'hero--hold');
  $('drillScore').textContent = `${got} / ${total || 0}`;
  const missed = D.queue.length + (D.pending && !D.answers.some(a => a.n === D.pending.n) ? 1 : 0); D.queue = []; D.pending = null;
  $('drillScoreSub').textContent = (stopped ? 'Drill stopped early. ' : ratio >= 0.75 ? 'You kept your money safe. ' : ratio >= 0.4 ? 'Some risky moments. Read the coaching below. ' : 'A scammer would have succeeded. Read the coaching below. ') + (missed ? `${missed} pressure point${missed > 1 ? 's' : ''} went unanswered.` : '');
  $('drillCoachTitle').textContent = t('coachTitle');
  const reasons = r ? ((r.reasons_user_language && r.reasons_user_language.length) ? r.reasons_user_language : r.reasons) : [];
  const sig = r ? Object.entries(r.signals || {}).filter(([, v]) => v).map(([k]) => SIGNAL_LABELS[k] || k) : [];
  $('drillCoach').innerHTML = [...reasons, ...(sig.length ? ['Signals: ' + sig.join(', ')] : [])].map(x => `<li>${esc(x)}</li>`).join('') || '<li class="muted">No risk signals were detected in this call.</li>';
  $('drillAnswers').innerHTML = D.answers.map(a => `<li><b>${esc(MARKER_TEXT[a.marker])}</b> You chose “${esc(t(a.choice))}” · ${esc(t(a.grade))}</li>`).join('') || '<li class="muted">No pressure points reached.</li>';
  show('drill');
  try { await api(`/api/sessions/${S.sid}/end`); } catch (e) {}
  stopCallUI(); setListening(false);
}
async function drillStop() { try { await api(`/api/sessions/${S.sid}/replay/stop`, 'POST'); } catch (e) {} drillFinish(true); }
async function drillLeave() { if (D.active) await drillStop(); try { await newSession(); } catch (e) {} $('drillSetup').hidden = false; $('drillRun').hidden = true; $('drillSummary').hidden = true; }

// ---------- wiring ----------
$('btnIncoming').onclick = startCall;
$('btnPay').onclick = () => { S.replayPayment = null; openPay(); };
$('btnMic').onclick = toggleMic;
$('btnUseScript').onclick = () => { $('micBanner').hidden = true; $('scriptSel').focus(); $('scriptSel').scrollIntoView({ block: 'center' }); };
$('btnEnableAudio').onclick = () => { S.caller.ensure(); S.guardian.ensure(); setTimeout(updateAudioBanner, 200); };
$('btnReplay').onclick = async () => { S.caller.ensure(); S.guardian.ensure(); connectCallWS(); const id = $('scriptSel').value; try { await api(`/api/sessions/${S.sid}/replay`, 'POST', { script_id: id, voice: true, pace: 1.0, stop_at_marker: 'payment_demand' }); log('auto-playing script ' + id); toast('Scripted caller is on the line'); } catch (e) { toast('Could not start the script: ' + e.message); } };
$('btnReplayStop').onclick = async () => { try { await api(`/api/sessions/${S.sid}/replay/stop`, 'POST'); toast('Script stopped'); } catch (e) {} };
$('btnOpenPay').onclick = openPay;
$('btnBackCall').onclick = () => show(S.callActive ? 'call' : 'home');
$('amountInp').addEventListener('input', updateAmountPreview);
$('amountInp').addEventListener('blur', () => { const a = parseAmount($('amountInp').value); $('amountInp').value = a ? fmtIndian(a) : ''; updateAmountPreview(); prewarmAmount(); });
$('vpaInp').addEventListener('input', () => setInvalid('fVpa', false));
$('amountInp').addEventListener('input', () => setInvalid('fAmt', false));
$('payForm').addEventListener('submit', (e) => { e.preventDefault(); sendPayment(); });
$('btnEndCall').onclick = endCall;
$('btnSend').onclick = sendPayment;
$('btnCancelPay').onclick = cancelPayment;
$('btnOverride').onclick = askOverride;
$('btnReplayVoice').onclick = replayVoice;
$('btnConfirmNo').onclick = () => closeSheet('confirmSheet');
$('btnConfirmYes').onclick = () => { if (parseAmount($('confirmAmount').value) !== Number(S.case.payment.amount_inr)) { setInvalid('fConfirm', true); $('confirmAmount').focus(); return; } doOverride('customer typed the amount and confirmed'); };
$('confirmAmount').addEventListener('input', () => setInvalid('fConfirm', false));
$('btnTalk').onclick = startTalk; $('btnTalkEnd').onclick = endTalk;
$('btnAccept').onclick = acceptCall; $('btnDecline').onclick = declineCall;
$('btnHome').onclick = () => { endTalk(); show('home'); };
$('btnDrill').onclick = () => { $('drillSetup').hidden = false; $('drillRun').hidden = true; $('drillSummary').hidden = true; show('drill'); };
$('btnDrillStart').onclick = drillStart; $('btnDrillStop').onclick = drillStop;
$('btnDrillBack').onclick = async () => { await drillLeave(); show('home'); };
$('btnDrillAgain').onclick = async () => { await drillLeave(); };
$('btnDrillHome').onclick = async () => { await drillLeave(); show('home'); };
$('userSel').onchange = () => { location.search = `?user=${$('userSel').value}`; };
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { if ($('confirmSheet').classList.contains('is-open')) closeSheet('confirmSheet'); } });
init().catch(e => { log('init failed: ' + e.message); renderBootError(e); });
