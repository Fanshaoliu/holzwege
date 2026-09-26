'use strict';
/* Chiptune engine: MML sequencer with NES-style pulse/triangle voices, noise drums and a soft echo, plus SFX.
   The music data lives in js/music.js. */
const Audio = (() => {
  let ctx = null, bgmGain = null, sfxGain = null, echoIn = null, cur = null, timer = null, waves = {}, noiseBuf = null;
  const compiled = {};

  /* ---------------- MML ---------------- */
  const PC = { c: 0, d: 2, e: 4, f: 5, g: 7, a: 9, b: 11 };
  function parseMML(src) {
    const s = src.replace(/\|/g, ' ');
    const ev = [], loops = [];
    let i = 0, oct = 4, len = 4, ldots = 0, vol = 12, gate = 7;
    const num = () => { const m = /^\d+/.exec(s.slice(i)); if (!m) return null; i += m[0].length; return parseInt(m[0], 10); };
    const dots = () => { let n = 0; while (s[i] === '.') { n++; i++; } return n; };
    const beats = (l, d) => { let b = 4 / l, add = b; for (let k = 0; k < d; k++) { add /= 2; b += add; } return b; };
    const length = () => { const l = num(); const d = dots(); return l === null ? beats(len, d || ldots) : beats(l, d); };
    while (i < s.length) {
      const c = s[i].toLowerCase();
      if (/\s/.test(c)) { i++; continue; }
      i++;
      if (c in PC) {
        let acc = 0;
        while (s[i] === '+' || s[i] === '#' || s[i] === '-') { acc += s[i] === '-' ? -1 : 1; i++; }
        ev.push({ midi: (oct + 1) * 12 + PC[c] + acc, b: length(), vol, gate });
      } else if (c === 'r') ev.push({ midi: -1, b: length(), vol, gate });
      else if (c === 'k' || c === 's' || c === 'h') ev.push({ drum: c, b: length(), vol, gate });
      else if (c === '&') { const b = length(); if (ev.length) ev[ev.length - 1].b += b; }
      else if (c === 'o') oct = num();
      else if (c === '<') oct--;
      else if (c === '>') oct++;
      else if (c === 'l') { len = num(); ldots = dots(); }
      else if (c === 'v') vol = num();
      else if (c === 'q') gate = num();
      else if (c === '[') loops.push(ev.length);
      else if (c === ']') {
        const n = num() || 2, from = loops.pop(), body = ev.slice(from);
        for (let k = 1; k < n; k++) body.forEach(e => ev.push(Object.assign({}, e)));
      }
    }
    return ev;
  }
  const VOICES = {
    lead: { wave: 'p25', vol: 0.07, a: 0.006, d: 0.14, s: 0.72, r: 0.06, vib: true },
    harm: { wave: 'p125', vol: 0.045, a: 0.006, d: 0.16, s: 0.65, r: 0.06 },
    arp: { wave: 'p25', vol: 0.03, a: 0.003, d: 0.09, s: 0.3, r: 0.03 },
    bass: { wave: 'triangle', vol: 0.16, a: 0.004, d: 0.06, s: 0.9, r: 0.03 },
    bell: { wave: 'triangle', vol: 0.13, a: 0.002, bell: 0.42, r: 0.05 },
    soft: { wave: 'triangle', vol: 0.11, a: 0.03, d: 0.25, s: 0.8, r: 0.15, vib: true },
  };
  function voiceFor(track, key) {
    const k = key.replace(/\d+$/, '');
    return VOICES[(track.voices && track.voices[k]) || k] || VOICES.lead;
  }
  function compile(name) {
    if (compiled[name]) return compiled[name];
    const tr = MUSIC.TRACKS[name];
    compiled[name] = { bpm: tr.bpm, ch: Object.entries(tr.ch).map(([k, src]) => ({ key: k, voice: voiceFor(tr, k), ev: parseMML(src) })) };
    return compiled[name];
  }
  function check() {
    const out = {};
    for (const name of Object.keys(MUSIC.TRACKS)) {
      out[name] = {};
      compile(name).ch.forEach(c => { out[name][c.key] = Math.round(c.ev.reduce((a, e) => a + e.b, 0) * 1000) / 1000; });
    }
    return out;
  }

  /* ---------------- synthesis ---------------- */
  function init() {
    if (ctx) return;
    try {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      bgmGain = ctx.createGain(); sfxGain = ctx.createGain();
      bgmGain.connect(ctx.destination); sfxGain.connect(ctx.destination);
      // a short, dark echo gives the pulse waves some room without losing the 8-bit character
      echoIn = ctx.createGain(); echoIn.gain.value = 0.2;
      const dl = ctx.createDelay(1), fb = ctx.createGain(), lp = ctx.createBiquadFilter();
      dl.delayTime.value = 0.23; fb.gain.value = 0.26; lp.type = 'lowpass'; lp.frequency.value = 2200;
      echoIn.connect(dl); dl.connect(lp); lp.connect(fb); fb.connect(dl); lp.connect(bgmGain);
      for (const [key, duty] of [['p125', 0.125], ['p25', 0.25], ['p50', 0.5]]) {
        const n = 48, re = new Float32Array(n + 1), im = new Float32Array(n + 1);
        for (let h = 1; h <= n; h++) re[h] = Math.sin(Math.PI * h * duty) / h;
        waves[key] = ctx.createPeriodicWave(re, im);
      }
      noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
      const d = noiseBuf.getChannelData(0);
      for (let k = 0; k < d.length; k++) d[k] = Math.random() * 2 - 1;
      setVolumes();
    } catch (e) { ctx = null; }
  }
  function unlock() { init(); if (ctx && ctx.state === 'suspended') ctx.resume(); }
  function setVolumes() { if (!ctx) return; bgmGain.gain.value = G.settings.bgm * 0.9; sfxGain.gain.value = G.settings.sfx; }
  function tone(type, f, t0, dur, vol, dest, slide) {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type; o.frequency.setValueAtTime(f, t0);
    if (slide) o.frequency.exponentialRampToValueAtTime(slide, t0 + dur);
    g.gain.setValueAtTime(0, t0);
    g.gain.linearRampToValueAtTime(vol, t0 + 0.01);
    g.gain.setValueAtTime(vol, t0 + Math.max(0.02, dur * 0.7));
    g.gain.linearRampToValueAtTime(0, t0 + dur);
    o.connect(g); g.connect(dest); o.start(t0); o.stop(t0 + dur + 0.02);
  }
  function note(v, midi, t0, len, level, dest) {
    const f = 440 * Math.pow(2, (midi - 69) / 12);
    const o = ctx.createOscillator(), g = ctx.createGain();
    if (waves[v.wave]) o.setPeriodicWave(waves[v.wave]); else o.type = v.wave;
    o.frequency.setValueAtTime(f, t0);
    const vol = v.vol * level;
    g.gain.setValueAtTime(0, t0);
    g.gain.linearRampToValueAtTime(vol, t0 + v.a);
    let end;
    if (v.bell) {
      g.gain.setTargetAtTime(0, t0 + v.a, v.bell);
      end = t0 + Math.max(len, v.bell * 3);
    } else {
      g.gain.setTargetAtTime(vol * v.s, t0 + v.a, v.d / 3);
      g.gain.setTargetAtTime(0, t0 + len, v.r / 3);
      end = t0 + len + v.r * 2;
    }
    if (v.vib && len > 0.32) {
      const lfo = ctx.createOscillator(), depth = ctx.createGain();
      lfo.frequency.value = 5.5;
      depth.gain.setValueAtTime(0, t0);
      depth.gain.linearRampToValueAtTime(0, t0 + 0.18);
      depth.gain.linearRampToValueAtTime(f * 0.006, t0 + 0.4);
      lfo.connect(depth); depth.connect(o.frequency);
      lfo.start(t0); lfo.stop(end);
    }
    o.connect(g); g.connect(dest);
    o.start(t0); o.stop(end + 0.02);
  }
  function drum(kind, t0, level, dest) {
    const src = ctx.createBufferSource(); src.buffer = noiseBuf;
    const f = ctx.createBiquadFilter(), g = ctx.createGain();
    const dur = kind === 'h' ? 0.04 : kind === 's' ? 0.13 : 0.09;
    f.type = kind === 'k' ? 'lowpass' : 'highpass';
    f.frequency.value = kind === 'h' ? 7000 : kind === 's' ? 1400 : 300;
    const vol = (kind === 'h' ? 0.05 : kind === 's' ? 0.13 : 0.12) * level;
    g.gain.setValueAtTime(vol, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + dur);
    src.connect(f); f.connect(g); g.connect(dest);
    src.start(t0, Math.random() * 0.5, dur + 0.02);
    if (kind === 'k') {
      const o = ctx.createOscillator(), og = ctx.createGain();
      o.type = 'triangle'; o.frequency.setValueAtTime(150, t0); o.frequency.exponentialRampToValueAtTime(45, t0 + 0.11);
      og.gain.setValueAtTime(0.32 * level, t0); og.gain.linearRampToValueAtTime(0, t0 + 0.13);
      o.connect(og); og.connect(dest); o.start(t0); o.stop(t0 + 0.15);
    }
  }

  /* ---------------- sequencer ---------------- */
  function play(name) {
    name = MUSIC.ALIAS[name] || name;
    if (cur && cur.name === name) return;
    stop();
    if (!name || name === 'none' || !MUSIC.TRACKS[name]) { cur = null; return; }
    init();
    if (!ctx) return;
    const tr = compile(name);
    const out = ctx.createGain(); out.connect(bgmGain); out.connect(echoIn);
    const t = ctx.currentTime + 0.12;
    cur = { name, spb: 60 / tr.bpm, out, ch: tr.ch.map(c => ({ c, i: 0, t })) };
    timer = setInterval(schedule, 30);
    schedule();
  }
  function schedule() {
    if (!cur || !ctx) return;
    const horizon = ctx.currentTime + 0.25;
    for (const p of cur.ch) {
      const ev = p.c.ev;
      if (!ev.length) continue;
      let guard = 0;
      while (p.t < horizon && guard++ < 256) {
        const e = ev[p.i];
        const dur = e.b * cur.spb;
        const level = e.vol / 12;
        if (e.drum) drum(e.drum, p.t, level, cur.out);
        else if (e.midi >= 0) note(p.c.voice, e.midi, p.t, Math.max(0.03, dur * e.gate / 8), level, cur.out);
        p.t += dur;
        p.i = (p.i + 1) % ev.length;
      }
    }
  }
  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
    if (cur && ctx) {
      const out = cur.out;
      out.gain.setTargetAtTime(0, ctx.currentTime, 0.08);
      setTimeout(() => { try { out.disconnect(); } catch (e) { /* already gone */ } }, 1200);
    }
    cur = null;
  }
  function noise(t0, dur, vol, hp) {
    const len = Math.floor(ctx.sampleRate * dur);
    const buf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
    const s = ctx.createBufferSource(); s.buffer = buf;
    const f = ctx.createBiquadFilter(); f.type = hp ? 'highpass' : 'lowpass'; f.frequency.value = hp || 900;
    const g = ctx.createGain(); g.gain.value = vol;
    s.connect(f); f.connect(g); g.connect(sfxGain); s.start(t0);
  }
  function sfx(name) {
    init();
    if (!ctx) return;
    const t = ctx.currentTime + 0.01;
    switch (name) {
      case 'blip': tone('square', 880, t, 0.03, 0.03, sfxGain); break;
      case 'confirm': tone('square', 660, t, 0.06, 0.06, sfxGain); tone('square', 990, t + 0.06, 0.08, 0.06, sfxGain); break;
      case 'cancel': tone('square', 440, t, 0.08, 0.05, sfxGain, 300); break;
      case 'cursor': tone('square', 1200, t, 0.025, 0.03, sfxGain); break;
      case 'hammer': noise(t, 0.08, 0.35, 2000); tone('square', 180, t, 0.06, 0.08, sfxGain); break;
      case 'break': noise(t, 0.25, 0.45, 800); tone('square', 300, t, 0.3, 0.07, sfxGain, 60); break;
      case 'splash': noise(t, 0.45, 0.35); break;
      case 'water': noise(t, 1.2, 0.18); break;
      case 'teleport': tone('square', 220, t, 0.35, 0.05, sfxGain, 1760); tone('sine', 1760, t + 0.3, 0.3, 0.05, sfxGain); break;
      case 'door': noise(t, 0.12, 0.2, 400); tone('triangle', 140, t, 0.1, 0.12, sfxGain); break;
      case 'bell': tone('sine', 523, t, 1.8, 0.12, sfxGain); tone('sine', 1046, t, 1.2, 0.05, sfxGain); tone('sine', 523, t + 0.9, 1.8, 0.1, sfxGain); break;
      case 'hit': noise(t, 0.12, 0.3, 1500); tone('square', 120, t, 0.1, 0.08, sfxGain, 60); break;
      case 'item': [523, 659, 784, 1046].forEach((f, i) => tone('square', f, t + i * 0.09, 0.12, 0.05, sfxGain)); break;
      case 'fanfare': [392, 523, 659, 784, 659, 784, 1046].forEach((f, i) => tone('square', f, t + i * 0.1, i === 6 ? 0.5 : 0.12, 0.06, sfxGain)); break;
      case 'codex': [784, 988, 1175].forEach((f, i) => tone('sine', f, t + i * 0.12, 0.4, 0.06, sfxGain)); break;
      case 'win': [523, 523, 523, 698, 880, 784, 880, 1046].forEach((f, i) => tone('square', f, t + i * 0.11, 0.1, 0.06, sfxGain)); break;
      case 'bump': tone('triangle', 90, t, 0.06, 0.1, sfxGain); break;
      case 'chest': tone('square', 330, t, 0.08, 0.05, sfxGain); tone('square', 494, t + 0.08, 0.2, 0.05, sfxGain); break;
      case 'speak': tone('sine', 262, t, 2.4, 0.1, sfxGain); tone('sine', 392, t + 0.2, 2.4, 0.07, sfxGain); tone('sine', 523, t + 0.4, 2.6, 0.06, sfxGain); break;
      default: break;
    }
  }
  return { play, stop, sfx, unlock, setVolumes, check, parseMML, get current() { return cur && cur.name; } };
})();
