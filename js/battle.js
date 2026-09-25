'use strict';
/* "心象对决" — Dragon Quest-style encounter screen where the right response is an understanding, not an attack. */
const Battle = (() => {
  const LABEL = { ask: '追问', listen: '倾听', silence: '沉默', wait: '等待', act: '动手', item: '宝物', teleport: '克洛伊·移位',
    analyze: '罐头·分析', moment: '眼下', attack: '攻击', flee: '逃跑', call: '呼唤' };
  let B = null, st = null;
  const M = { waiting: null, lines: [] };

  function bars() {
    $('b-hp').style.width = `${Math.max(0, st.hp / st.max * 100)}%`;
    $('b-mind').style.width = `${Math.max(0, st.mind)}%`;
  }
  function line(text, cls) {
    const box = $('b-msg');
    const el = document.createElement('span'); el.className = 'l' + (cls ? ' ' + cls : '');
    el.textContent = fmt(text);
    box.appendChild(el);
    while (box.children.length > 4) box.removeChild(box.firstChild);
  }
  function waitConfirm() { return new Promise(res => { M.waiting = res; }); }
  function confirm() { if (M.waiting) { const r = M.waiting; M.waiting = null; r(); return true; } return false; }
  async function msg(lines) {
    if (!lines || !lines.length) return;
    $('b-cmd').classList.add('hidden');
    $('b-msg').innerHTML = '';
    for (let i = 0; i < lines.length; i++) {
      line(lines[i]);
      if (i < lines.length - 1) await Promise.race([sleep(520), waitConfirm()]);
      M.waiting = null;
    }
    const nx = document.createElement('span'); nx.className = 'l'; nx.style.color = '#f6cc5a'; nx.textContent = '▼';
    $('b-msg').appendChild(nx);
    await waitConfirm();
  }

  function enemyImg() { return $('b-enemy').querySelector('img'); }
  function sizeEnemy() {
    const im = enemyImg(); if (!im.naturalWidth) return;
    const area = $('b-enemy');
    const s = Math.max(1, Math.floor(Math.min(area.clientHeight * 0.95 / im.naturalHeight, area.clientWidth * 0.8 / im.naturalWidth)));
    im.style.width = `${im.naturalWidth * s}px`; im.style.height = `${im.naturalHeight * s}px`;
  }

  function commands() {
    if (B.menu) return B.menu.slice();
    const list = ['ask', 'listen', 'silence', 'wait', 'act', 'item'];
    if (G.party.includes('chloe')) list.push('teleport');
    if (G.party.includes('tin')) list.push('analyze');
    if (B.extra && counterOk(B.extra.req)) list.splice(4, 0, B.extra.key);
    return list;
  }
  function counterOk(req) {
    const m = req.match(/^(\w+)>=(\d+)$/); if (!m) return false;
    return (st.counters[m[1]] || 0) >= parseInt(m[2], 10);
  }
  function label(k) { return (B.extra && k === B.extra.key) ? B.extra.label : LABEL[k]; }

  function chooseCommand() {
    return new Promise(res => {
      const box = $('b-cmd'); box.innerHTML = ''; box.classList.remove('hidden');
      const ph = phase();
      const idle = (ph && ph.idleWait) || B.idleWait;
      let timer = null;
      const done = (k) => { clearTimeout(timer); box.classList.add('hidden'); UI.clearNav(); res(k); };
      const arm = () => { clearTimeout(timer); if (idle) timer = setTimeout(() => done('wait'), idle); };
      const btns = commands().map(k => UI.mkOpt(label(k), () => {
        if (k === 'item') { clearTimeout(timer); itemMenu(done, () => { chooseCommand().then(res); }); }
        else done(k);
      }));
      btns.forEach(b => box.appendChild(b));
      UI.setNav(btns, { grid: 2 });
      st.arm = arm; arm();
    });
  }
  function itemMenu(done, back) {
    const box = $('b-cmd'); box.innerHTML = '';
    const ids = Object.keys(G.items).filter(k => G.items[k] > 0 && window.ITEMS[k] && k !== 'coin');
    const btns = ids.map(k => UI.mkOpt(window.ITEMS[k].name, () => done('item:' + k)));
    const bk = UI.mkOpt('返回', () => back());
    btns.push(bk);
    btns.forEach(b => box.appendChild(b));
    UI.setNav(btns, { grid: 2, back: () => back() });
  }

  function phase() { return B.phases ? B.phases[st.phase] : null; }
  function response(key) {
    const ph = phase();
    let list;
    if (key.indexOf('item:') === 0) {
      const id = key.slice(5);
      list = (ph && ph.items && ph.items[id]) || (B.items && B.items[id]) || (ph && ph.cmds && ph.cmds.item) || B.cmds.item;
    } else list = (ph && ph.cmds && ph.cmds[key]) || B.cmds[key];
    if (!list) list = [{ t: ['……'], dmg: 0 }];
    const uk = st.phase + ':' + key;
    const u = st.uses[uk] || 0; st.uses[uk] = u + 1;
    return list[Math.min(u, list.length - 1)];
  }

  async function apply(r) {
    await msg(r.t);
    if (r.dmg) {
      st.hp = Math.max(0, Math.min(st.max, st.hp - r.dmg));
      if (r.dmg > 0) { Audio.sfx('hit'); const e = $('b-enemy'); e.classList.remove('hit'); void e.offsetWidth; e.classList.add('hit'); }
    }
    if (r.hurt) { st.mind -= r.hurt; UI.shake(); }
    if (r.heal) st.mind = Math.min(100, st.mind + r.heal);
    if (r.inc) st.counters[r.inc] = (st.counters[r.inc] || 0) + 1;
    if (r.set) G.flags[r.set] = 1;
    bars();
  }
  async function enemyTurn() {
    const ph = phase();
    const list = (ph && ph.enemy) || B.enemy;
    const e = list[st.enemyIdx % list.length]; st.enemyIdx++;
    await msg(e.t);
    if (e.hurt) { st.mind -= e.hurt; if (e.hurt >= 10) UI.shake(); bars(); }
  }
  async function checkPhase() {
    if (!B.phases) return;
    while (st.phase < B.phases.length - 1 && st.hp <= B.phases[st.phase].until) {
      st.phase++;
      const ph = B.phases[st.phase];
      if (ph.enter) { UI.flash(); await msg(ph.enter); }
    }
  }

  async function finale() {
    UI.flash(); Audio.stop(); Audio.sfx('speak');
    $('b-msg').innerHTML = '';
    await sleep(900);
    const el = document.createElement('span'); el.className = 'l'; el.style.cssText = 'font-size:1.5em;color:#fff3cf;text-align:center;margin-top:0.6em';
    el.textContent = `${G.name}：${B.speakLine}`;
    $('b-msg').appendChild(el);
    await sleep(600);
    await waitConfirm();
    $('b-enemy').classList.add('fade');
    await sleep(1300);
  }

  async function run() {
    for (;;) {
      const key = await chooseCommand();
      const r = response(key);
      await apply(r);
      if (r.speak) { await finale(); return 'win'; }
      if (st.hp <= 0 || r.win) return 'win';
      await checkPhase();
      if (!r.noEnemy) {
        await enemyTurn();
        if (st.mind <= 0) {
          if (B.noRetreat) { await msg(B.retreatText || ['……']); st.mind = 40; bars(); }
          else { await msg(['心绪乱成了一团……']); return 'retreat'; }
        }
      }
    }
  }

  async function start(id) {
    if (window.AUTO_BATTLE) return 'win';
    B = window.BATTLES[id];
    st = { hp: B.hp, max: B.hp, mind: 100, uses: {}, counters: {}, phase: 0, enemyIdx: 0 };
    const prevMode = G.mode;
    G.mode = 'battle';
    Audio.sfx('hit');
    await UI.fade('out', 220);
    $('battle').classList.remove('hidden');
    $('b-enemy').classList.remove('fade', 'hit');
    const im = enemyImg();
    if (B.sprite) {
      im.style.display = '';
      im.onload = sizeEnemy;
      im.src = `assets/monsters/${B.sprite}.png`;
      if (im.complete) sizeEnemy();
    } else { im.style.display = 'none'; }
    $('b-name').textContent = B.name || '　';
    $('b-top').style.visibility = B.sprite ? 'visible' : 'hidden';
    $('b-msg').innerHTML = '';
    bars();
    Audio.play(id === 'noone' ? 'boss' : id === 'nothing' ? 'none' : 'battle');
    await UI.fade('in', 220);
    await msg(B.intro);
    const res = await run();
    if (res === 'win') {
      if (B.sprite && id !== 'noone') { $('b-enemy').classList.add('fade'); Audio.sfx('win'); await sleep(700); }
      if (B.win && B.win.length) await msg(B.win);
    }
    await UI.fade('out', 260);
    $('battle').classList.add('hidden');
    UI.clearNav();
    G.mode = prevMode === 'battle' ? 'scene' : prevMode;
    if (G.map) Audio.play(G.map.music);
    await UI.fade('in', 260);
    return res;
  }

  return { start, confirm, get waiting() { return !!M.waiting; }, poke() { if (st && st.arm) st.arm(); } };
})();
