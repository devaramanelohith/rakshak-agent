// Shared audio, websocket, formatting and icon helpers for the Rakshak pages.
const WS_BASE = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host;

function b64ToInt16(b64) {
  const bin = atob(b64); const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Int16Array(bytes.buffer);
}
function downsample(f32, srcRate, dstRate) {
  if (srcRate === dstRate) { const o = new Int16Array(f32.length); for (let i = 0; i < f32.length; i++) o[i] = Math.max(-1, Math.min(1, f32[i])) * 32767; return o; }
  const ratio = srcRate / dstRate, n = Math.floor(f32.length / ratio), out = new Int16Array(n);
  for (let i = 0; i < n; i++) {
    const start = Math.floor(i * ratio), end = Math.min(f32.length, Math.floor((i + 1) * ratio));
    let s = 0, c = 0; for (let j = start; j < end; j++) { s += f32[j]; c++; }
    out[i] = Math.max(-1, Math.min(1, c ? s / c : 0)) * 32767;
  }
  return out;
}
// RMS level (0..1) of a PCM16 chunk, for VU meters.
function rms16(int16) { let s = 0; for (let i = 0; i < int16.length; i++) { const v = int16[i] / 32768; s += v * v; } return int16.length ? Math.sqrt(s / int16.length) : 0; }

class Player {
  constructor() { this.ctx = null; this.gain = null; this.next = 0; this.onState = null; }
  ensure() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)(); this.gain = this.ctx.createGain(); this.gain.connect(this.ctx.destination);
      this.ctx.onstatechange = () => this.onState && this.onState(this.ctx.state);
    }
    if (this.ctx.state === 'suspended') this.ctx.resume().catch(() => {});
    return this.ctx;
  }
  blocked() { return !!this.ctx && this.ctx.state !== 'running'; }
  play(int16, rate) {
    const ctx = this.ensure();
    const f = new Float32Array(int16.length); for (let i = 0; i < int16.length; i++) f[i] = int16[i] / 32768;
    const buf = ctx.createBuffer(1, f.length, rate); buf.copyToChannel(f, 0);
    const src = ctx.createBufferSource(); src.buffer = buf; src.connect(this.gain);
    const t = Math.max(ctx.currentTime + 0.03, this.next); src.start(t); this.next = t + buf.duration;
    return buf.duration;
  }
  duck(level, seconds) { if (!this.gain) return; const g = this.gain.gain, t = this.ctx.currentTime; g.cancelScheduledValues(t); g.setValueAtTime(level, t); g.setValueAtTime(1, t + seconds); }
  flush() { this.next = 0; }
}

class Mic {
  constructor(onChunk) { this.onChunk = onChunk; this.ctx = null; this.stream = null; this.node = null; this.on = false; }
  async start() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { const e = new Error('This browser does not support microphone capture.'); e.kind = 'unsupported'; throw e; }
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 } });
    } catch (err) {
      const e = new Error(err && err.message ? err.message : String(err));
      e.kind = (err && (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError' || err.name === 'SecurityError')) ? 'denied' : (err && err.name === 'NotFoundError') ? 'nodevice' : 'other';
      throw e;
    }
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    await this.ctx.audioWorklet.addModule('/static/worklet.js');
    const src = this.ctx.createMediaStreamSource(this.stream);
    this.node = new AudioWorkletNode(this.ctx, 'pcm-capture');
    this.node.port.onmessage = (e) => { if (this.on) this.onChunk(downsample(e.data, this.ctx.sampleRate, 16000)); };
    src.connect(this.node); this.on = true;
  }
  stop() { this.on = false; if (this.stream) this.stream.getTracks().forEach(t => t.stop()); if (this.ctx) this.ctx.close(); this.ctx = null; }
}

function openWS(path, { onJson, onBinary, onOpen, onClose } = {}) {
  const ws = new WebSocket(WS_BASE + path); ws.binaryType = 'arraybuffer';
  ws.onopen = () => onOpen && onOpen(ws);
  ws.onclose = () => onClose && onClose();
  ws.onmessage = (ev) => { if (ev.data instanceof ArrayBuffer) { onBinary && onBinary(ev.data); } else { try { onJson && onJson(JSON.parse(ev.data)); } catch (e) { console.warn(e); } } };
  return ws;
}
async function api(path, method = 'GET', body) {
  let r;
  try {
    r = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  } catch (err) { const e = new Error('Cannot reach the Rakshak server'); e.network = true; throw e; }
  if (!r.ok) throw new Error(path + ' ' + r.status + ' ' + (await r.text()));
  return r.json();
}
function fmtINR(n) { return '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 }); }
function esc(s) { return String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function riskBand(r) { return r >= 0.7 ? 'high' : r >= 0.45 ? 'elevated' : 'low'; }
function riskColor(r) { return getComputedStyle(document.documentElement).getPropertyValue(`--c-band-${riskBand(r)}`).trim() || (r >= 0.7 ? '#c62828' : r >= 0.45 ? '#a8570a' : '#1b7f4b'); }
function qs(k) { return new URLSearchParams(location.search).get(k); }
function fmtClock(sec) { sec = Math.max(0, Math.floor(sec)); return `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`; }
function relTime(ts) { const s = Math.max(0, (Date.now() / 1000) - ts); if (s < 60) return `${Math.round(s)} s ago`; if (s < 3600) return `${Math.round(s / 60)} min ago`; if (s < 86400) return `${Math.round(s / 3600)} h ago`; return `${Math.round(s / 86400)} d ago`; }

// Copy with a visible result on the triggering button.
async function copyText(text, btn) {
  try { await navigator.clipboard.writeText(text); if (btn) { const old = btn.textContent; btn.textContent = 'Copied'; setTimeout(() => btn.textContent = old, 1400); } return true; }
  catch (e) { if (btn) btn.textContent = 'Copy failed'; return false; }
}

// Inline SVG icons (stroke = currentColor). Usage: icon('shield')
const ICONS = {
  shield: '<path d="M12 3l8 3v6c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/>',
  shieldOff: '<path d="M12 3l8 3v6c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V6l8-3z"/><path d="M9 9l6 6M15 9l-6 6"/>',
  phone: '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z"/>',
  phoneOff: '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z"/><path d="M3 3l18 18"/>',
  mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0014 0M12 18v3"/>',
  micOff: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0014 0M12 18v3M3 3l18 18"/>',
  pay: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M7 15h3"/>',
  alert: '<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v4M12 17.5v.5"/>',
  warn: '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16v.5"/>',
  check: '<path d="M4 12l5 5L20 7"/>',
  checkCircle: '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  xCircle: '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.5"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0116 0"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2 20a7 7 0 0114 0M16 4a3.5 3.5 0 010 7M22 20a7 7 0 00-6-6.9"/>',
  bell: '<path d="M6 16V11a6 6 0 0112 0v5l2 2H4l2-2z"/><path d="M10 20a2 2 0 004 0"/>',
  play: '<path d="M7 5v14l12-7z"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="1.5"/>',
  replay: '<path d="M4 12a8 8 0 1 0 3-6.2"/><path d="M4 4v5h5"/>',
  arrowLeft: '<path d="M19 12H5M11 18l-6-6 6-6"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
  ear: '<path d="M6 10a6 6 0 0112 0c0 3-2 4-3 6s-1 4-3 4-2-1-2-2"/><path d="M9.5 10a2.5 2.5 0 015 0c0 1.5-1.5 2-1.5 3.5"/>',
  wave: '<path d="M3 12h2l2-5 3 10 3-14 3 14 2-5h3"/>',
  graduation: '<path d="M2 9l10-5 10 5-10 5L2 9z"/><path d="M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/>',
  wifiOff: '<path d="M2 8a16 16 0 0120 0M5 12a11 11 0 0114 0M8.5 15.5a6 6 0 017 0"/><path d="M12 19v.5M3 3l18 18"/>',
  volumeX: '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16 9l5 6M21 9l-5 6"/>',
  volume: '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16 8a5 5 0 010 8M18.5 5.5a9 9 0 010 13"/>',
  speak: '<path d="M4 4h16v11H9l-5 4V4z"/><path d="M8 9h8M8 12h5"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 012-2h10"/>',
  print: '<path d="M6 9V3h12v6M6 17H4a2 2 0 01-2-2v-4a2 2 0 012-2h16a2 2 0 012 2v4a2 2 0 01-2 2h-2"/><rect x="6" y="14" width="12" height="7"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.5M3 12h.5M3 18h.5"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  bolt: '<path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/>',
  message: '<path d="M4 5h16v11H8l-4 4V5z"/>',
  link: '<path d="M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1"/>',
  tool: '<path d="M14.7 6.3a4 4 0 00-5 5L4 17v3h3l5.7-5.7a4 4 0 005-5l-2.4 2.4-2.1-2.1 2.5-2.3z"/>',
  sparkles: '<path d="M12 3l1.8 4.7L18.5 9l-4.7 1.8L12 15.5l-1.8-4.7L5.5 9l4.7-1.3L12 3z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"/>',
  hand: '<path d="M7 11V6a1.5 1.5 0 013 0v5M10 10V4.5a1.5 1.5 0 013 0V11M13 10.5V6a1.5 1.5 0 013 0v6"/><path d="M16 12v-1a1.5 1.5 0 013 0v4a6 6 0 01-6 6h-1.5a6 6 0 01-4.8-2.4L4 15a1.5 1.5 0 012.4-1.8L7 14"/>',
  question: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 015 0c0 1.5-2.5 2-2.5 3.5M12 17v.5"/>',
};
function icon(name, cls = '') { return `<svg class="ico ${cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONS[name] || ''}</svg>`; }
