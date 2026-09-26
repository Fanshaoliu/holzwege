'use strict';
/* 8-bit arrangements of public-domain classical pieces, written in MML.
   Per channel: o<n> octave, < > octave down/up, l<n> default length, notes a-g (+/# sharp, - flat) with length and dots,
   r rest, &<len> tie, [ ... ]<n> repeat, q<1-8> gate, v<0-15> volume. Drum channel: k kick, s snare, h hat.
   All channels of a track must add up to the same number of beats (checked by tests/music_check.py). */
const MUSIC = (() => {
  // Bach, Prelude in C major BWV 846: each bar is one five-note chord broken as 1 2 3 4 5 3 4 5, twice
  const preludeBars = [
    'o4 c o4 e o4 g o5 c o5 e', 'o4 c o4 d o4 a o5 d o5 f', 'o3 b o4 d o4 g o5 d o5 f', 'o4 c o4 e o4 g o5 c o5 e',
    'o4 c o4 e o4 a o5 e o5 a', 'o4 c o4 d o4 f+ o4 a o5 d', 'o3 b o4 d o4 g o5 d o5 g', 'o3 b o4 c o4 e o4 g o5 c',
    'o3 a o4 c o4 e o4 g o5 c', 'o3 d o3 a o4 d o4 f+ o5 c', 'o3 g o3 b o4 d o4 g o4 b', 'o3 g o3 b- o4 e o4 g o5 c+',
    'o3 f o3 a o4 d o4 a o5 d', 'o3 f o3 a- o4 d o4 f o4 b', 'o3 e o3 g o4 c o4 g o5 c', 'o3 e o3 f o3 a o4 c o4 f',
    'o3 d o3 f o3 a o4 c o4 f', 'o2 g o3 d o3 g o3 b o4 f', 'o3 c o3 e o3 g o4 c o4 e',
  ];
  const split = (b) => { const t = b.split(' '); const n = []; for (let i = 0; i < t.length; i += 2) n.push(t[i] + ' ' + t[i + 1]); return n; };
  const preludeLead = 'l16 ' + preludeBars.map(b => { const n = split(b); const half = [n[0], n[1], n[2], n[3], n[4], n[2], n[3], n[4]].join(' '); return half + ' ' + half; }).join(' | ');
  const preludeBass = preludeBars.map(b => { const n = split(b)[0].split(' '); return `o${+n[0].slice(1) - 1} ${n[1]}1`; }).join(' | ');
  // Beethoven, Für Elise: A section, first ending, A again, second ending, B section
  const eliseA = 'o5 e d+ e o4 b o5 d c | o4 a8 r o4 c e a | o4 b8 r e g+ b | o5 c8 r o4 e o5 e d+ | o5 e d+ e o4 b o5 d c | o4 a8 r o4 c e a | o4 b8 r e o5 c o4 b';
  const eliseBell = `l16 ${eliseA} | o4 a8 r r o5 e d+ | ${eliseA} | o4 a8 r o4 b o5 c d | ` +
    'o5 e8. o4 g o5 f e | o5 d8. o4 f o5 e d | o5 c8. o4 e o5 d c | o4 b8 r o4 e o5 e d+';
  const LA = 'o2 a o3 e a r8.', LE = 'o2 e o3 e g+ r8.';
  const eliseBassA = `r4. | ${LA} | ${LE} | ${LA} | r4. | ${LA} | ${LE}`;
  const eliseBass = `l16 ${eliseBassA} | ${LA} | ${eliseBassA} | ${LA} | o3 c g o4 c r8. | o2 g o3 g b r8. | ${LA} | o2 e o3 e o4 e r8.`;

  const TRACKS = {
    // Pachelbel, Canon in D
    canon: { bpm: 80, ch: {
      bass: 'l4 [o3 d o2 a b f+ g d g a]4',
      lead: 'l4 o5 f+ e d c+ o4 b a b o5 c+ | o5 d c+ o4 b a g f+ g e | l8 o5 d f+ a g f+ d f+ e d o4 b o5 d a g b a g | ' +
            'l16 o5 f+ d e f+ e c+ d e d o4 b o5 c+ d c+ o4 a b o5 c+ o4 b g a b a f+ g a g b a g a o5 c+ e a',
      harm: 'l1 r r | l4 o4 f+ e d c+ o3 b a b o4 c+ | o4 d c+ o3 b a g f+ g e | l8 o4 d f+ a g f+ d f+ e d o3 b o4 d a g b a g',
    } },
    // Brahms, Wiegenlied Op. 49 No. 4
    lullaby: { bpm: 92, ch: {
      bell: 'o5 g2 e8 e8 | g2 e8 g8 | o6 c4 o5 b4. a8 | a4 g4 d8 e8 | f4 d4 d8 e8 | f2 d8 f8 | b8 a8 g4 b4 | o6 c4 o5 r4 e8 e8',
      bass: 'q6 o3 c4 g4 g4 | c4 g4 g4 | o2 f4 o3 c4 c4 | c4 g4 g4 | o2 g4 o3 d4 d4 | o2 g4 o3 d4 f4 | o2 g4 b4 o3 d4 | o3 c4 g4 o2 g4',
      arp: 'o4 r4 e8 g8 e8 g8 | r4 e8 g8 e8 g8 | r4 f8 a8 f8 a8 | r4 e8 g8 e8 g8 | r4 f8 b8 f8 b8 | r4 f8 b8 f8 b8 | r4 d8 f8 d8 f8 | r4 e8 g8 c8 e8',
    } },
    // Petzold, Minuet in G (from Anna Magdalena's notebook)
    minuet: { bpm: 132, ch: {
      lead: 'l8 o5 d4 o4 g a b o5 c | o5 d4 o4 g4 g4 | o5 e4 c d e f+ | o5 g4 o4 g4 g4 | o5 c4 d c o4 b a | o4 b4 o5 c o4 b a g | o4 f+4 g a b g | o4 a2. | ' +
            'o5 d4 o4 g a b o5 c | o5 d4 o4 g4 g4 | o5 e4 c d e f+ | o5 g4 o4 g4 g4 | o5 c4 d c o4 b a | o4 b4 o5 c o4 b a g | o4 a4 b a g f+ | o4 g2.',
      bass: 'o2 g2 o3 d4 | o2 g2 o3 d4 | o3 c2 g4 | o2 g2 o3 d4 | o2 a2 o3 e4 | o2 g2 o3 d4 | o3 d2 a4 | o3 d2 o2 a4 | ' +
            'o2 g2 o3 d4 | o2 g2 o3 d4 | o3 c2 g4 | o2 g2 o3 d4 | o2 a2 o3 e4 | o2 g2 o3 d4 | o3 d2 o2 a4 | o2 g2.',
      arp: 'q4 l8 [o3 b o4 d g d o3 b o4 d]2 o3 g o4 c e c o3 g o4 c | o3 b o4 d g d o3 b o4 d | o3 a o4 c e c o3 a o4 c | o3 b o4 d g d o3 b o4 d | [o3 a o4 d f+ d o3 a o4 d]2 | ' +
           '[o3 b o4 d g d o3 b o4 d]2 o3 g o4 c e c o3 g o4 c | o3 b o4 d g d o3 b o4 d | o3 a o4 c e c o3 a o4 c | o3 b o4 d g d o3 b o4 d | o3 a o4 d f+ d o3 a o4 c | o3 b o4 d g d o3 b o4 d',
    } },
    // Mozart, Rondo alla Turca K. 331
    rondo: { bpm: 126, ch: {
      lead: 'l16 o5 c8 r8 d c o4 b o5 c | o5 e8 r8 f e d+ e | o5 b a g+ a b a g+ a | o6 c4 o5 a8 o6 c8 | o5 b8 a8 g8 a8 | o5 b8 a8 g8 a8 | o5 b8 a8 g8 f+8 | o5 e4 o4 b a g+ a | ' +
            'o5 c8 r8 d c o4 b o5 c | o5 e8 r8 f e d+ e | o5 b a g+ a b a g+ a | o6 c4 o5 a8 o6 c8 | o5 b8 a8 g+8 a8 | o5 e8 f8 d8 o4 b8 | o5 c8 e8 o4 b8 g+8 | o4 a4 b a g+ a',
      bass: 'l8 o2 a o3 e o2 a o3 e | o2 a o3 e o2 a o3 e | o2 e b e b | o2 a o3 e o2 a o3 e | o2 e b e b | o3 c g c g | o2 b o3 f+ o2 b o3 f+ | o2 e b e b | ' +
            'o2 a o3 e o2 a o3 e | o2 a o3 e o2 a o3 e | o2 e b e b | o2 a o3 e o2 a o3 e | o2 e b e b | o3 d a d a | o2 e b e b | o2 a o3 e o2 a4',
      drum: '[k8 h8 s8 h8]16',
    } },
    // Bach, Jesu, Joy of Man's Desiring BWV 147
    jesu: { bpm: 64, ch: {
      lead: '[l12 o4 g a b o5 d c c e d d | o5 g f+ g d o4 b g a b o5 c | o5 d e d c o4 b a b g a | o4 d f+ a o5 c o4 b a g4]2',
      harm: 'l1 r r r | l12 o3 g a b o4 d c c e d d | o4 g f+ g d o3 b g a b o4 c | o4 d e d c o3 b a b g a | o3 d f+ a o4 c o3 b a g4',
      bass: '[o2 g4 o3 c4 o2 b4 | o2 e4 g4 a4 | o2 b4 a4 o3 d4 | o3 d4 c4 o2 g4]2',
    } },
    // Grieg, Peer Gynt: Morning Mood (flute, then the oboe answers)
    morning: { bpm: 84, ch: {
      lead: 'l8 o5 b g+ f+ e f+ g+ | b g+ f+ e f+ g+ | b g+ b o6 c+ o5 g+ o6 c+ | o5 b g+ f+ e4. | r2. | r2. | r2. | r2.',
      harm: 'r2. | r2. | r2. | r2. | l8 o4 b g+ f+ e f+ g+ | b g+ f+ e f+ g+ | b g+ b o5 c+ o4 g+ o5 c+ | o4 b g+ f+ e4.',
      bass: '[o2 e2. | e2. | a2. | b4. e4.]2',
      arp: 'q5 l8 [o3 b o4 e g+ b g+ e | o3 b o4 e g+ b g+ e | o3 a o4 c+ e a e c+ | o3 b o4 d+ f+ e g+ b]2',
    } },
    // Satie, Gymnopédie No. 1
    gymnopedie: { bpm: 76, voices: { lead: 'soft' }, ch: {
      lead: 'r2. | r2. | r2. | r2. | r4 o5 f+4 a4 | o5 g4 f+4 c+4 | o4 b4 o5 c+4 d4 | o4 a2. | o4 f+2.&2. | r2. | r2. | ' +
            'r4 o5 f+4 a4 | o5 g4 f+4 c+4 | o4 b4 o5 c+4 d4 | o4 a2. | o4 f+2.&2. | r2. | r2.',
      bass: '[o2 g2. o2 d2.]10',
      arp: '[r4 o4 d2 r4 o4 c+2]10',
      harm: '[r4 o4 f+2]20',
    } },
    // Dvořák, Symphony No. 9, Largo ("Going Home")
    largo: { bpm: 76, ch: {
      lead: 'o5 f+4. a8 a2 | f+4. e8 d2 | e4. f+8 a4. f+8 | e1 | f+4. a8 a2 | f+4. e8 d2 | e4. f+8 e4. d8 | d1',
      bass: 'o3 d2 o2 a2 | b2 f+2 | a2 o3 e2 | o2 a2 o3 c+2 | o3 d2 o2 a2 | g2 o3 d2 | o2 a2 g2 | o3 d1',
      arp: 'q5 l8 o4 d f+ a f+ d f+ a f+ | o3 b o4 d f+ d o3 b o4 d f+ d | o3 a o4 c+ e c+ o3 a o4 c+ e c+ | o3 a o4 c+ e c+ o3 a o4 c+ e c+ | ' +
           'o4 d f+ a f+ d f+ a f+ | o3 g b o4 d o3 b g b o4 d o3 b | o3 a o4 c+ e g e c+ o3 a o4 c+ | o4 d f+ a f+ d f+ a f+',
    } },
    // Johann Strauss II, The Blue Danube
    danube: { bpm: 152, ch: {
      lead: 'o4 d4 f+4 a4 | a2. | r2. | r2 d4 | d4 f+4 a4 | a2. | r2. | r2 c+4 | c+4 e4 b4 | b2. | r2. | r2 c+4 | c+4 e4 b4 | b2. | r2. | r2 d4 | ' +
            'd4 f+4 a4 | o5 d2. | r2. | r2 o4 d4 | d4 f+4 a4 | o5 d2. | r2. | r2 o4 d4',
      harm: 'r2. | r2. | r4 o5 a4 a4 | r4 f+4 f+4 | r2. | r2. | r4 a4 a4 | r4 g4 g4 | r2. | r2. | r4 b4 b4 | r4 g4 g4 | r2. | r2. | r4 b4 b4 | r4 f+4 f+4 | ' +
            'r2. | r2. | r4 o6 d4 d4 | r4 o5 a4 a4 | r2. | r2. | r4 o6 d4 d4 | r4 o5 b4 b4',
      bass: 'q6 [o2 d4 a4 a4]6 [o2 a4 o3 e4 e4]9 o2 d4 a4 a4 [o2 d4 a4 a4]6 [o2 g4 o3 d4 d4]2',
      arp: 'q5 [r4 o3 f+4 f+4]6 [r4 o3 g4 g4]9 r4 o3 f+4 f+4 [r4 o3 f+4 f+4]6 [r4 o3 b4 b4]2',
    } },
    // Mozart, Eine kleine Nachtmusik K. 525
    nachtmusik: { bpm: 132, ch: {
      lead: 'o4 g4 r8 d8 g4 r8 d8 | o4 g8 d8 g8 b8 o5 d4 r4 | o5 c4 r8 o4 a8 o5 c4 r8 o4 a8 | o5 c8 o4 a8 f+8 a8 d4 r4 | ' +
            'o4 g4 r8 d8 g4 r8 d8 | o4 g8 d8 g8 b8 o5 d4 r4 | o5 c8 o4 a8 f+8 a8 o5 d8 c8 o4 b8 a8 | o4 g4 d4 g4 r4',
      bass: 'o3 g4 r8 d8 g4 r8 d8 | o3 g8 d8 g8 b8 o4 d4 r4 | o3 c4 r8 o2 a8 o3 c4 r8 o2 a8 | o3 c8 o2 a8 f+8 a8 d4 r4 | ' +
            'o3 g4 r8 d8 g4 r8 d8 | o3 g8 d8 g8 b8 o4 d4 r4 | o2 d8 a8 d8 a8 d8 a8 d8 f+8 | o2 g4 d4 g4 r4',
    } },
    // Beethoven, Für Elise
    elise: { bpm: 75, ch: { bell: eliseBell, bass: eliseBass } },
    // Bach, Prelude in C major BWV 846 (Well-Tempered Clavier I)
    prelude: { bpm: 80, ch: { lead: preludeLead, bass: preludeBass } },
    // Tchaikovsky, Swan Lake, Act II scene
    swan: { bpm: 72, ch: {
      lead: 'o4 f+2 o3 b8 o4 c+8 d8 e8 | o4 f+4. d8 f+4. d8 | o4 f+4. o3 b8 o4 d8 o3 b8 g8 o4 d8 | o3 b1 | ' +
            'o5 f+2 o4 b8 o5 c+8 d8 e8 | o5 f+4. d8 f+4. d8 | o5 f+4. o4 b8 o5 d8 o4 b8 g8 o5 d8 | o4 b1',
      bass: '[o2 b1 | b1 | g1 | f+2 b2]2',
      arp: 'q5 l16 [[o3 f+ b o4 d o3 b]8 [o3 g b o4 d o3 b]4 [o3 f+ b o4 d o3 b]4]2',
    } },
    // Beethoven, "Moonlight" Sonata, first movement
    moonlight: { bpm: 52, voices: { lead: 'soft' }, ch: {
      arp: 'q6 l12 [[o3 g+ o4 c+ e]8 [o3 a o4 c+ e]2 [o3 a o4 d f+]2 o3 g+ b+ o4 f+ o3 g+ o4 c+ e o3 g+ o4 c+ d+ o3 f+ b+ o4 d+]2',
      bass: '[o3 c+1 | o2 b1 | a2 f+2 | g+1]2',
      lead: 'r1 | r1 | r1 | r1 | r2 r4 r8. o4 g+16 | o4 g+2. r8. g+16 | o4 a2 f+2 | o4 g+1',
    } },
    // Grieg, Peer Gynt: In the Hall of the Mountain King
    mountain: { bpm: 168, ch: {
      lead: 'l8 o3 b o4 c+ d e f+ d f+4 | o4 f c+ f4 e c e4 | o3 b o4 c+ d e f+ d f+ b | o4 a f+ d f+ a2 | ' +
            'o4 b o5 c+ d e f+ d f+4 | o5 f c+ f4 e c e4 | o4 b o5 c+ d e f+ d f+ b | o5 a f+ d f+ a2',
      bass: 'q4 [o2 b4 f+4 b4 f+4 | o3 c+4 o2 g+4 o3 c4 o2 g4 | o2 b4 f+4 b4 f+4 | o3 d4 o2 a4 f+4 a4]2',
      drum: '[k8 h8 s8 h8 k8 k8 s8 h8]8',
    } },
    // Bach, Toccata and Fugue in D minor BWV 565
    toccata: { bpm: 132, ch: {
      lead: 'o5 a16 g16 a2. r8 | o5 g16 f16 e16 d16 c+8 d2 r8 | o4 a16 g16 a2. r8 | o4 e8 f8 c+8 d2 r8 | o3 a16 g16 a2. r8 | o3 g16 f16 e16 d16 c+8 d2 r8 | ' +
            'l16 o3 c+ e g b- o4 c+ e g b- o5 c+ e g b- o6 c+4 | o6 d o5 a f d o4 a f d o3 a f d o2 a f o2 d4 | ' +
            '[o4 a o5 d f d]4 | [o4 b- o5 d f d]4 | [o4 g b- o5 d o4 b-]4 | [o4 a o5 c+ e c+]4 | [o4 a o5 d f d]4 | [o4 b- o5 d g d]4 | [o4 g o5 c+ e c+]4 | ' +
            'o5 e d c+ o4 b- a g f e d c+ d e f g a o5 c+',
      harm: 'l1 r r r r r r r r | o5 a16 g16 a2. r8 | o5 g16 f16 e16 d16 c+8 d2 r8 | r1 | r1 | o5 a16 g16 a2. r8 | o5 g16 f16 e16 d16 c+8 d2 r8 | r1 | r1',
      bass: '[o2 d1]6 o2 c+1 d1 | l8 [o2 d o3 d]4 [o2 b- o3 b-]4 [o2 g o3 g]4 [o2 a o3 a]4 [o2 d o3 d]4 [o2 b- o3 b-]4 [o2 a o3 a]4 [o2 a o3 a]4',
      drum: 'l1 r r r r r r r r | [k8 h8 s8 h8 k8 k8 s8 h8]8',
    } },
  };

  const ALIAS = {
    title: 'canon', ending: 'canon', home: 'lullaby', village: 'minuet', tavern: 'rondo', shrine: 'jesu', core: 'jesu',
    forest: 'morning', clearing: 'gymnopedie', night: 'gymnopedie', world: 'largo', harbor: 'danube', harbor_in: 'nachtmusik',
    tower: 'elise', capital: 'prelude', capital_in: 'prelude', archive: 'prelude', backup: 'swan', sad: 'swan',
    ruins: 'moonlight', battle: 'mountain', boss: 'toccata',
  };
  return { TRACKS, ALIAS };
})();
