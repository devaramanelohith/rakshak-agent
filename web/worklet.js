// AudioWorklet: batches mic float32 frames and posts them to the main thread.
class PCMCapture extends AudioWorkletProcessor {
  constructor() { super(); this.buf = []; this.n = 0; }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    this.buf.push(new Float32Array(ch)); this.n += ch.length;
    if (this.n >= 2048) {
      const out = new Float32Array(this.n); let o = 0;
      for (const b of this.buf) { out.set(b, o); o += b.length; }
      this.port.postMessage(out, [out.buffer]);
      this.buf = []; this.n = 0;
    }
    return true;
  }
}
registerProcessor('pcm-capture', PCMCapture);
