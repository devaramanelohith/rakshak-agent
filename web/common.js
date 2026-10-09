// Shared audio + websocket helpers for the Rakshak demo pages.
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

class Player {
  constructor() { this.ctx = null; this.gain = null; this.next = 0; }
  ensure() {
    if (!this.ctx) { this.ctx = new (window.AudioContext || window.webkitAudioContext)(); this.gain = this.ctx.createGain(); this.gain.connect(this.ctx.destination); }
    if (this.ctx.state === 'suspended') this.ctx.resume();
    return this.ctx;
  }
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
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 } });
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
  const r = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  if (!r.ok) throw new Error(path + ' ' + r.status + ' ' + (await r.text()));
  return r.json();
}
function fmtINR(n) { return '₹' + Number(n).toLocaleString('en-IN'); }
function esc(s) { return String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function riskColor(r) { return r >= 0.7 ? '#e5484d' : r >= 0.45 ? '#f5a524' : '#30a46c'; }
function qs(k) { return new URLSearchParams(location.search).get(k); }
