'use strict';
/* Tiny chiptune synthesizer: square/triangle voices, a look-ahead sequencer, and SFX. */
const Audio = (() => {
  let ctx = null, bgmGain = null, sfxGain = null, cur = null, timer = null, nextTime = 0, pos = [];
  const NOTE = { C: 0, 'C#': 1, Db: 1, D: 2, 'D#': 3, Eb: 3, E: 4, F: 5, 'F#': 6, Gb: 6, G: 7, 'G#': 8, Ab: 8, A: 9, 'A#': 10, Bb: 10, B: 11 };
  function freq(n) {
    const m = n.match(/^([A-G][#b]?)(\d)$/);
    if (!m) return 0;
    return 440 * Math.pow(2, (NOTE[m[1]] + (parseInt(m[2], 10) + 1) * 12 - 69) / 12);
  }
  function parse(s) {
    return s.replace(/\|/g, ' ').trim().split(/\s+/).map(t => { const [n, d] = t.split(':'); return [n, parseFloat(d || '1')]; });
  }
  const V = { lead: ['square', 0.055], bass: ['triangle', 0.13], arp: ['square', 0.028], pad: ['sine', 0.05], bell: ['sine', 0.07] };
  const TRACKS = {
    title: { bpm: 84, ch: {
      lead: 'A4:2 D5:2 F#5:3 E5:1 | D5:2 B4:2 A4:4 | G4:2 B4:2 D5:3 C#5:1 | B4:2 A4:2 F#4:4 | A4:2 D5:2 F#5:3 A5:1 | G5:2 F#5:2 E5:4 | D5:2 E5:2 F#5:2 G5:2 | F#5:3 E5:1 D5:4',
      bass: 'D3:4 A3:4 | G2:4 D3:4 | E3:4 B3:4 | F#3:4 D3:4 | D3:4 A3:4 | G3:4 E3:4 | B2:4 G2:4 | A2:4 D3:4',
      arp: 'D4:1 F#4:1 A4:1 F#4:1 D4:1 F#4:1 A4:1 F#4:1 | G3:1 B3:1 D4:1 B3:1 G3:1 B3:1 D4:1 B3:1 | E4:1 G4:1 B4:1 G4:1 E4:1 G4:1 B4:1 G4:1 | F#3:1 A3:1 D4:1 A3:1 F#3:1 A3:1 D4:1 A3:1 | D4:1 F#4:1 A4:1 F#4:1 D4:1 F#4:1 A4:1 F#4:1 | G3:1 B3:1 E4:1 B3:1 G3:1 B3:1 E4:1 B3:1 | B3:1 D4:1 G4:1 D4:1 B3:1 D4:1 G4:1 D4:1 | A3:1 C#4:1 E4:1 C#4:1 D4:1 F#4:1 A4:1 F#4:1' } },
    village: { bpm: 100, ch: {
      lead: 'F5:2 A5:1 C6:3 | Bb5:2 A5:1 G5:3 | A5:2 F5:1 D5:2 E5:1 | F5:6 | C5:2 F5:1 A5:3 | G5:2 E5:1 C5:3 | D5:2 E5:1 F5:2 G5:1 | F5:6',
      bass: 'F3:3 C4:3 | Bb2:3 F3:3 | D3:3 A3:3 | F3:3 C4:3 | F3:3 A3:3 | C3:3 G3:3 | Bb2:3 C3:3 | F3:6' } },
    forest: { bpm: 70, ch: {
      lead: 'D5:4 F5:2 E5:2 | A4:6 -:2 | D5:2 E5:2 F5:2 G5:2 | E5:6 -:2 | F5:4 E5:2 D5:2 | C5:4 A4:4 | Bb4:2 C5:2 D5:4 | A4:8',
      bass: 'D3:8 | A2:8 | Bb2:8 | A2:8 | D3:8 | F2:8 | G2:8 | A2:8',
      arp: 'D4:2 A4:2 F4:2 A4:2 | C#4:2 E4:2 A4:2 E4:2 | D4:2 F4:2 Bb4:2 F4:2 | C#4:2 E4:2 A4:2 E4:2 | D4:2 A4:2 F4:2 A4:2 | C4:2 F4:2 A4:2 F4:2 | D4:2 G4:2 Bb4:2 G4:2 | C#4:2 E4:2 A4:2 E4:2' } },
    world: { bpm: 112, ch: {
      lead: 'C5:2 C5:1 D5:1 E5:2 G5:2 | F5:2 E5:1 D5:1 E5:4 | D5:2 D5:1 E5:1 F5:2 A5:2 | G5:6 -:2 | C6:2 B5:1 A5:1 G5:2 E5:2 | F5:2 E5:1 D5:1 C5:4 | D5:2 E5:1 F5:1 E5:2 D5:2 | C5:6 -:2',
      bass: 'C3:2 G3:2 C3:2 G3:2 | F2:2 C3:2 C3:2 G2:2 | G2:2 D3:2 F2:2 C3:2 | G2:2 D3:2 G2:2 B2:2 | A2:2 E3:2 C3:2 G3:2 | F2:2 C3:2 A2:2 E3:2 | G2:2 D3:2 G2:2 B2:2 | C3:2 G3:2 C3:4' } },
    harbor: { bpm: 126, ch: {
      lead: 'G5:2 B5:1 D6:2 B5:1 | C6:2 A5:1 F#5:3 | G5:2 B5:1 A5:2 G5:1 | E5:3 D5:3 | G5:2 B5:1 D6:2 E6:1 | D6:2 B5:1 G5:3 | A5:2 C6:1 B5:2 A5:1 | G5:6',
      bass: 'G3:3 D3:3 | C3:3 D3:3 | G3:3 E3:3 | C3:3 D3:3 | G3:3 B2:3 | G3:3 E3:3 | D3:3 D3:3 | G2:6' } },
    capital: { bpm: 96, ch: {
      arp: 'A4:1 E5:1 A5:1 E5:1 A4:1 E5:1 A5:1 E5:1 | F4:1 C5:1 F5:1 C5:1 F4:1 C5:1 F5:1 C5:1 | G4:1 D5:1 G5:1 D5:1 G4:1 D5:1 G5:1 D5:1 | E4:1 B4:1 E5:1 G#5:1 E4:1 B4:1 E5:1 B4:1',
      lead: 'E5:8 | C5:8 | D5:8 | B4:6 -:2',
      bass: 'A2:8 | F2:8 | G2:8 | E2:8' } },
    night: { bpm: 64, ch: {
      bell: 'C5:3 A4:1 F4:4 | G4:3 A4:1 Bb4:4 | A4:3 G4:1 F4:2 D4:2 | C4:8 | F4:3 G4:1 A4:4 | Bb4:3 A4:1 G4:4 | A4:2 C5:2 Bb4:2 G4:2 | F4:8',
      bass: 'F3:8 | C3:8 | D3:8 | C3:8 | F3:8 | G2:8 | C3:8 | F2:8' } },
    battle: { bpm: 150, ch: {
      lead: 'C5:1 C5:1 G5:2 F5:1 Eb5:1 D5:2 | Eb5:1 F5:1 G5:2 C5:4 | Ab5:1 G5:1 F5:2 Eb5:1 D5:1 C5:2 | D5:1 Eb5:1 F5:2 G5:4',
      bass: 'C3:1 C4:1 C3:1 C4:1 C3:1 C4:1 C3:1 C4:1 | Ab2:1 Ab3:1 Ab2:1 Ab3:1 Ab2:1 Ab3:1 Ab2:1 Ab3:1 | F2:1 F3:1 F2:1 F3:1 F2:1 F3:1 F2:1 F3:1 | G2:1 G3:1 G2:1 G3:1 G2:1 G3:1 B2:1 B3:1' } },
    boss: { bpm: 138, ch: {
      lead: 'E5:2 G5:2 B5:3 A5:1 | G5:2 F#5:2 E5:4 | C5:2 E5:2 G5:3 F#5:1 | E5:2 D#5:2 B4:4',
      bass: 'E2:1 E3:1 E2:1 E3:1 E2:1 E3:1 E2:1 E3:1 | C2:1 C3:1 C2:1 C3:1 C2:1 C3:1 C2:1 C3:1 | A1:1 A2:1 A1:1 A2:1 A1:1 A2:1 A1:1 A2:1 | B1:1 B2:1 B1:1 B2:1 B1:1 B2:1 D#2:1 D#3:1',
      arp: 'E4:1 B4:1 E4:1 B4:1 G4:1 B4:1 G4:1 B4:1 | C4:1 G4:1 C4:1 G4:1 E4:1 G4:1 E4:1 G4:1 | A3:1 E4:1 A3:1 E4:1 C4:1 E4:1 C4:1 E4:1 | B3:1 F#4:1 B3:1 F#4:1 D#4:1 F#4:1 D#4:1 F#4:1' } },
    drone: { bpm: 52, ch: {
      pad: 'A2:8 | A2:8 | F2:8 | E2:8',
      bell: '-:4 E5:4 | -:6 C5:2 | -:4 A4:4 | -:8' } },
  };
  const ALIAS = { home: 'village', tavern: 'harbor', shrine: 'night', clearing: 'forest', harbor_in: 'harbor', tower: 'capital',
    capital_in: 'capital', archive: 'capital', backup: 'night', ruins: 'drone', core: 'drone', ending: 'title', sad: 'night' };

  function init() {
    if (ctx) return;
    try {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      bgmGain = ctx.createGain(); sfxGain = ctx.createGain();
      bgmGain.connect(ctx.destination); sfxGain.connect(ctx.destination);
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
  function play(name) {
    name = ALIAS[name] || name;
    if (cur && cur.name === name) return;
    stop();
    if (!name || name === 'none' || !TRACKS[name]) { cur = null; return; }
    init();
    if (!ctx) return;
    const tr = TRACKS[name];
    cur = { name, bpm: tr.bpm, ch: Object.entries(tr.ch).map(([k, s]) => ({ voice: k, notes: parse(s) })) };
    pos = cur.ch.map(() => ({ i: 0, t: ctx.currentTime + 0.1 }));
    timer = setInterval(schedule, 40);
    schedule();
  }
  function schedule() {
    if (!cur || !ctx) return;
    const eighth = 60 / cur.bpm / 2;
    const horizon = ctx.currentTime + 0.25;
    cur.ch.forEach((c, k) => {
      const p = pos[k];
      while (p.t < horizon) {
        const [n, d] = c.notes[p.i];
        const dur = d * eighth;
        if (n !== '-') {
          const [type, vol] = V[c.voice];
          const f = freq(n);
          if (f) tone(type, f, p.t, dur * (c.voice === 'bell' ? 1.6 : 0.92), vol, bgmGain);
        }
        p.t += dur; p.i = (p.i + 1) % c.notes.length;
      }
    });
  }
  function stop() { if (timer) clearInterval(timer); timer = null; cur = null; }
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
  return { play, stop, sfx, unlock, setVolumes, get current() { return cur && cur.name; } };
})();
