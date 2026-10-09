// Victim-side bank app. State: session, websockets, audio.
const S = { sid: null, userId: 'demo-user', profile: null, evWS: null, callWS: null, mic: null, callStart: null, timer: null,
            caller: new Player(), guardian: new Player(), lastRubric: null, case: null, countdownT: null, guardianWS: null, guardianMic: null, guardianPlayer: new Player(), replayPayment: null };
const $ = (id) => document.getElementById(id);
function show(view) { document.querySelectorAll('.view').forEach(v => v.classList.remove('active')); $('view-' + view).classList.add('active'); }
function log(msg) { const el = $('log'); el.textContent = `[${new Date().toLocaleTimeString()}] ${msg}\n` + el.textContent.slice(0, 6000); }
function toast(msg, ms = 2600) { const t = $('toast'); t.textContent = msg; t.style.display = 'block'; clearTimeout(t._h); t._h = setTimeout(() => t.style.display = 'none', ms); }
setInterval(() => { $('clock').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }, 1000);

async function init() {
  S.userId = qs('user') || 'demo-user';
  $('userSel').value = S.userId;
  const snap = await api('/api/sessions', 'POST', { session_id: qs('session') || null, user_id: S.userId, mode: 'audio' });
  S.sid = snap.session_id; S.profile = snap.profile;
  $('sidText').textContent = S.sid;
  const link = `/scammer?session=${S.sid}`; $('scammerLink').href = link; $('scammerLink2').href = link;
  $('homeName').textContent = `Namaste, ${S.profile.name}`;
  $('langSel').value = S.profile.language || 'hi'; $('contactInp').value = S.profile.trusted_contact_name || ''; $('guardianChk').checked = !!S.profile.guardian_enabled;
  const scripts = await api('/api/scripts');
  $('scriptSel').innerHTML = scripts.map(s => `<option value="${s.id}">${esc(s.title)} (${s.language})</option>`).join('');
  connectEvents();
  log(`session ${S.sid} ready for ${S.profile.name}`);
}

function connectEvents() {
  S.evWS = openWS(`/ws/events/${S.sid}`, { onJson: onEvent, onClose: () => setTimeout(connectEvents, 1500) });
}
function onEvent(ev) {
  switch (ev.type) {
    case 'hello': if (ev.snapshot) { ev.snapshot.turns.forEach(addTranscript); if (ev.snapshot.rubric) renderRubric(ev.snapshot.rubric); } break;
    case 'transcript': addTranscript(ev.turn); break;
    case 'risk_update': renderRubric(ev.rubric); log(`risk ${Math.round(ev.rubric.risk_score * 100)}% stage=${ev.rubric.stage} (${ev.rubric.latency_ms} ms)`); break;
    case 'whisper': $('whisperBanner').textContent = ev.text; $('whisperBanner').style.display = 'block'; log('whisper: ' + ev.text); break;
    case 'agent_running': $('payStatus').innerHTML = '<span class="spinner"></span>Rakshak is checking the payee and the call…'; break;
    case 'decision': onDecision(ev); break;
    case 'case_update': if (S.case && ev.case.case_id === S.case.case_id) S.case = ev.case; break;
    case 'replay_paused': case 'replay_finished': S.replayPayment = ev.payment_attempt; if (S.replayPayment) toast('Scripted caller is demanding payment — tap "Open UPI pay"'); log('replay reached payment demand'); break;
    case 'replay_marker': log('script marker: ' + ev.marker); break;
    case 'party_joined': log('party joined: ' + ev.role); break;
    case 'call_ended': stopCallUI(); break;
    case 'analysis_error': log('analysis error: ' + ev.error); break;
  }
}
function addTranscript(turn) {
  const el = $('transcript'); if (el.querySelector('.muted')) el.innerHTML = '';
  const d = document.createElement('div'); d.className = 't ' + turn.speaker; d.innerHTML = `<b>${turn.speaker === 'caller' ? 'Caller' : 'You'}</b> · ${esc(turn.text)}`; el.appendChild(d); el.scrollTop = el.scrollHeight;
}
function renderRubric(r) {
  S.lastRubric = r; const pct = Math.round(r.risk_score * 100);
  $('riskPct').textContent = pct + '%'; $('riskBar').style.width = pct + '%'; $('riskBar').style.background = riskColor(r.risk_score);
  $('signalChips').innerHTML = Object.entries(r.signals || {}).filter(([, v]) => v).map(([k]) => `<span>${k.replace(/_/g, ' ')}</span>`).join('');
  const reasons = (r.reasons_user_language && r.reasons_user_language.length ? r.reasons_user_language : r.reasons) || [];
  $('reasons').innerHTML = reasons.slice(0, 4).map(x => `<li>${esc(x)}</li>`).join('');
}

// ---------- call ----------
async function startCall() {
  show('call'); $('callerNum').textContent = '+91 98765 00301';
  S.callStart = Date.now(); clearInterval(S.timer);
  S.timer = setInterval(() => { const s = Math.floor((Date.now() - S.callStart) / 1000); $('callTimer').textContent = `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`; }, 1000);
  S.caller.ensure(); S.guardian.ensure();
  connectCallWS();
}
function connectCallWS() {
  if (S.callWS && S.callWS.readyState === 1) return;
  S.callWS = openWS(`/ws/call/${S.sid}/user`, {
    onBinary: (buf) => S.caller.play(new Int16Array(buf), 16000),
    onJson: (m) => {
      if (m.type === 'rakshak_audio' && m.audio_b64) { S.caller.duck(0.15, 8); S.guardian.play(b64ToInt16(m.audio_b64), m.rate || 16000); }
      if (m.type === 'caller_audio' && m.audio_b64) { S.caller.play(b64ToInt16(m.audio_b64), m.rate || 16000); }
    },
    onOpen: () => log('call audio channel open'),
  });
}
async function toggleMic() {
  if (S.mic) { S.mic.stop(); S.mic = null; $('micPill').textContent = 'mic off'; $('micPill').className = 'pill'; return; }
  try {
    S.mic = new Mic((int16) => { if (S.callWS && S.callWS.readyState === 1) S.callWS.send(int16.buffer); });
    await S.mic.start(); $('micPill').textContent = 'mic live'; $('micPill').className = 'pill live'; log('microphone streaming (16 kHz)');
  } catch (e) { toast('Mic unavailable: ' + e.message); S.mic = null; }
}
function stopCallUI() { clearInterval(S.timer); if (S.mic) { S.mic.stop(); S.mic = null; } $('micPill').textContent = 'mic off'; $('micPill').className = 'pill'; }
async function endCall() { try { await api(`/api/sessions/${S.sid}/end`); } catch (e) {} stopCallUI(); show('home'); }

// ---------- payment ----------
function openPay() {
  show('pay');
  const p = S.replayPayment; if (p) { $('vpaInp').value = p.vpa; $('payeeNameInp').value = p.payee_name || ''; $('amountInp').value = p.amount_inr; }
  $('payCallNote').textContent = S.lastRubric ? `Call in progress · current scam risk ${Math.round(S.lastRubric.risk_score * 100)}%` : 'Call in progress';
  $('payStatus').textContent = '';
}
async function sendPayment() {
  const vpa = $('vpaInp').value.trim(), name = $('payeeNameInp').value.trim(), amount = Number($('amountInp').value);
  if (!vpa || !amount) return toast('Enter payee and amount');
  $('btnSend').disabled = true; $('payStatus').innerHTML = '<span class="spinner"></span>Checking with Rakshak…';
  S.guardian.ensure();
  try {
    const res = await api('/api/payments', 'POST', { session_id: S.sid, vpa, payee_name: name, amount_inr: amount });
    if (!S.case || S.case.case_id !== res.case.case_id) onDecision({ case: res.case, audio_b64: res.audio_b64, spoken_text: res.spoken_text, audio_rate: 16000 });
  } catch (e) { toast('Payment check failed: ' + e.message); log(e.message); }
  $('btnSend').disabled = false;
}
function onDecision(ev) {
  const c = ev.case; S.case = c; const d = c.decision;
  log(`decision ${d.action} (${d.decided_by}, conf ${d.confidence}) in ${d.latency_ms || '-'} ms`);
  if (ev.audio_b64) { S.caller.duck(0.1, 20); S.guardian.play(b64ToInt16(ev.audio_b64), ev.audio_rate || 16000); }
  if (d.action === 'proceed') { show('done'); $('doneTitle').textContent = 'Payment sent'; $('doneBody').innerHTML = `${fmtINR(c.payment.amount_inr)} to <b>${esc(c.payment.vpa)}</b><div class="muted">Rakshak saw no coercion on the call and the payee looks ordinary (score ${c.policy.score}).</div>`; return; }
  show('hold');
  const warn = d.action === 'warn';
  $('holdHead').className = 'hold-head' + (warn ? ' warn' : ''); $('holdTitle').textContent = warn ? 'Please double-check this payment' : 'Payment paused for your safety';
  $('holdSub').textContent = `${fmtINR(c.payment.amount_inr)} to ${c.payment.vpa}`;
  $('spokenText').textContent = ev.spoken_text || d.user_message || '';
  $('holdReasons').innerHTML = (d.reasons || []).map(r => `<li>${esc(r)}</li>`).join('');
  const p = c.payee || {};
  $('payeeCard').innerHTML = [['Risk band', `<b style="color:${p.risk_band === 'critical' || p.risk_band === 'high' ? '#ff8a8e' : '#fff'}">${p.risk_band || '-'}</b>`], ['Mule score', p.mule_risk_score ?? '-'], ['Payers in last 48h', p.fan_in_48h ?? '-'], ['Cash-out ratio (7d)', p.cash_out_ratio_7d ?? '-'], ['Dormant before burst', (p.dormant_days_before_burst ?? '-') + ' days'], ['Telecom risk (FRI)', p.fri_level || '-'], ['1930 complaints', p.linked_complaints_1930 ?? 0], ['Account age', (p.account_age_days ?? '-') + ' days']].map(([k, v]) => `<span class="muted">${k}</span><span>${v}</span>`).join('');
  if (c.alert) { $('alertLine').style.display = 'block'; $('alertLine').innerHTML = `📣 <b>${esc(c.alert.contact_name)}</b> has been notified (${c.alert.channels.join(', ')}).`; } else { $('alertLine').style.display = 'none'; }
  $('btnOverride').textContent = warn ? 'Continue payment' : 'I know this person — pay anyway';
  $('btnCancelPay').textContent = warn ? 'Cancel payment' : 'Cancel payment & report';
  clearInterval(S.countdownT);
  if (!warn) { const end = (c.hold_until || (Date.now() / 1000 + 1800)) * 1000; const tick = () => { const s = Math.max(0, Math.floor((end - Date.now()) / 1000)); $('countdown').textContent = `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`; }; tick(); S.countdownT = setInterval(tick, 1000); } else { $('countdown').textContent = ''; }
}
async function cancelPayment() { if (!S.case) return; await api(`/api/cases/${S.case.case_id}/cancel`, 'POST'); clearInterval(S.countdownT); show('done'); $('doneTitle').textContent = 'Payment cancelled'; $('doneBody').innerHTML = `Nothing was sent. The bank's fraud desk has the case <b>${S.case.case_id}</b> and the payee is being reported.<div class="muted" style="margin-top:6px">You can hang up now. No officer ever asks for money on a call.</div>`; }
function askOverride() { if (!S.case) return; if (S.case.decision.action === 'warn') return doOverride('customer continued after warning'); $('confirmText').textContent = `You are about to send ${fmtINR(S.case.payment.amount_inr)} to ${S.case.payment.vpa}. Rakshak believes this is a scam. ${S.case.alert ? S.case.alert.contact_name + ' has been told.' : ''}`; $('confirmAmount').value = ''; $('confirmModal').classList.add('show'); }
async function doOverride(reason) { const c = S.case; await api(`/api/cases/${c.case_id}/override`, 'POST', { reason }); clearInterval(S.countdownT); $('confirmModal').classList.remove('show'); show('done'); $('doneTitle').textContent = 'Payment sent (override)'; $('doneBody').innerHTML = `${fmtINR(c.payment.amount_inr)} to <b>${esc(c.payment.vpa)}</b> after your explicit confirmation.<div class="muted" style="margin-top:6px">The override is recorded on case ${c.case_id}; the fraud desk will still review the payee.</div>`; }

// ---------- post-hold voice conversation (Gemini Live) ----------
async function startTalk() {
  if (!S.case) return; $('talkBox').style.display = 'block'; $('talkLog').innerHTML = '<div class="muted">Connecting to Rakshak…</div>';
  S.guardianPlayer.ensure();
  S.guardianWS = openWS(`/ws/guardian/${S.case.case_id}`, {
    onBinary: (buf) => S.guardianPlayer.play(new Int16Array(buf), 24000),
    onJson: (m) => {
      if (m.type === 'guardian_ready') { $('talkLog').innerHTML = ''; startGuardianMic(); }
      if (m.type === 'guardian_text') appendTalk('Rakshak', m.text);
      if (m.type === 'user_text') appendTalk('You', m.text);
      if (m.type === 'interrupted') S.guardianPlayer.flush();
      if (m.type === 'tool') { log('guardian tool: ' + m.name); if (m.name === 'request_release') askOverride(); if (m.name === 'call_trusted_contact') toast('Calling ' + (S.profile.trusted_contact_name || 'trusted contact') + '…'); if (m.name === 'keep_hold') toast('Hold kept. You are safe.'); }
      if (m.type === 'error') appendTalk('system', m.error);
    },
    onClose: () => { if (S.guardianMic) { S.guardianMic.stop(); S.guardianMic = null; } },
  });
}
let _talkLast = { who: null, el: null };
function appendTalk(who, text) { const el = $('talkLog'); if (_talkLast.who === who && _talkLast.el) { _talkLast.el.textContent += text; } else { const d = document.createElement('div'); d.className = 't ' + (who === 'You' ? 'user' : 'caller'); d.textContent = `${who}: ${text}`; el.appendChild(d); _talkLast = { who, el: d }; } el.scrollTop = el.scrollHeight; }
async function startGuardianMic() { try { S.guardianMic = new Mic((int16) => { if (S.guardianWS && S.guardianWS.readyState === 1) S.guardianWS.send(int16.buffer); }); await S.guardianMic.start(); } catch (e) { appendTalk('system', 'mic unavailable: ' + e.message); } }
function endTalk() { if (S.guardianWS) { try { S.guardianWS.send(JSON.stringify({ type: 'end' })); S.guardianWS.close(); } catch (e) {} } if (S.guardianMic) { S.guardianMic.stop(); S.guardianMic = null; } $('talkBox').style.display = 'none'; }

// ---------- wiring ----------
$('btnIncoming').onclick = startCall;
$('btnPay').onclick = () => { S.replayPayment = null; openPay(); };
$('btnMic').onclick = toggleMic;
$('btnReplay').onclick = async () => { S.caller.ensure(); S.guardian.ensure(); connectCallWS(); const id = $('scriptSel').value; await api(`/api/sessions/${S.sid}/replay`, 'POST', { script_id: id, voice: true, pace: 1.0, stop_at_marker: 'payment_demand' }); log('auto-playing script ' + id); };
$('btnOpenPay').onclick = openPay;
$('btnBackCall').onclick = () => show('call');
$('btnEndCall').onclick = endCall;
$('btnSend').onclick = sendPayment;
$('btnCancelPay').onclick = cancelPayment;
$('btnOverride').onclick = askOverride;
$('btnConfirmNo').onclick = () => $('confirmModal').classList.remove('show');
$('btnConfirmYes').onclick = () => { if (Number($('confirmAmount').value) !== Number(S.case.payment.amount_inr)) return toast('Type the exact amount to confirm'); doOverride('customer typed the amount and confirmed'); };
$('btnTalk').onclick = startTalk; $('btnTalkEnd').onclick = endTalk;
$('btnHome').onclick = () => { endTalk(); show('home'); };
$('btnSaveProfile').onclick = async () => { S.profile = await api(`/api/profiles/${S.userId}`, 'PUT', { language: $('langSel').value, trusted_contact_name: $('contactInp').value, guardian_enabled: $('guardianChk').checked }); $('guardianPill').className = 'pill ' + (S.profile.guardian_enabled ? 'on' : ''); $('guardianPill').textContent = S.profile.guardian_enabled ? 'Rakshak ON' : 'Rakshak OFF'; toast('Profile saved'); };
$('userSel').onchange = () => { location.search = `?user=${$('userSel').value}`; };
init().catch(e => { log('init failed: ' + e.message); });
