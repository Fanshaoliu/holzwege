'use strict';
/* Windows, dialog, menus, title, panels. All HTML overlays; navigation works with keys, taps and clicks. */
const UI = (() => {
  const PORTRAITS = new Set(['hero', 'chloe', 'tin', 'hof', 'ister', 'sera', 'sera_faceless', 'deca', 'gest', 'gest_faceless', 'fried', 'rena',
    'otto', 'marta', 'bato', 'molly', 'hans', 'greta', 'pip', 'lily', 'priest', 'woodcutter', 'lucy', 'coinlady', 'museumman', 'echo',
    'faceless', 'knewit', 'youth', 'sailor']);
  const S = { typing: false, full: '', shown: 0, resolve: null, nav: null, dlgTimer: null };

  function portraitKey(who) {
    if (!who || who === 'aether') return null;
    if (who === 'sera') return (G.flags.sera_eyes || G.flags.c4_sera_restored) ? 'sera' : 'sera_faceless';
    if (who === 'gest') return (G.flags.gest_faceless && !G.flags.c5_boss_won) ? 'gest_faceless' : 'gest';
    return PORTRAITS.has(who) ? who : null;
  }

  /* ---------------- dialog ---------------- */
  function say(line) {
    if (window.AUTO) { S.log = (S.log || []); S.log.push((line.name || '') + '：' + fmt(line.text)); return Promise.resolve(); }
    return new Promise(res => {
      const dlg = $('dlg');
      dlg.classList.remove('hidden', 'narr', 'aether', 'hero');
      const face = $('dlg-face');
      const pk = line.narr ? null : portraitKey(line.who);
      if (pk) { face.classList.remove('hidden'); face.querySelector('img').src = `assets/portraits/${pk}.png`; }
      else face.classList.add('hidden');
      let name = line.narr ? '' : fmt(line.name || '');
      if (line.tone) name += `（${line.tone}）`;
      $('dlg-name').textContent = name;
      if (line.narr) dlg.classList.add('narr');
      if (line.who === 'aether') dlg.classList.add('aether');
      if (line.who === 'hero') dlg.classList.add('hero');
      S.full = fmt(line.text); S.shown = 0; S.typing = true; S.resolve = res; S.narr = !!line.narr;
      $('dlg-text').textContent = '';
      $('dlg-next').classList.add('hidden');
      if (S.dlgTimer) clearInterval(S.dlgTimer);
      const per = [0, 1, 2, 4][G.settings.speed || 2];
      S.dlgTimer = setInterval(() => {
        if (!S.typing) return;
        S.shown = Math.min(S.full.length, S.shown + per);
        $('dlg-text').textContent = S.full.slice(0, S.shown);
        if (!S.narr && S.shown % 3 === 0) Audio.sfx('blip');
        if (S.shown >= S.full.length) finishType();
      }, 28);
    });
  }
  function finishType() {
    S.typing = false; clearInterval(S.dlgTimer); S.dlgTimer = null;
    $('dlg-text').textContent = S.full; $('dlg-next').classList.remove('hidden');
  }
  function advance() {
    if (S.typing) { finishType(); return true; }
    if (S.resolve) { const r = S.resolve; S.resolve = null; $('dlg-next').classList.add('hidden'); r(); return true; }
    return false;
  }
  function hideDialog() { $('dlg').classList.add('hidden'); $('choice').classList.add('hidden'); }
  function dialogActive() { return !!S.resolve || S.typing; }

  /* ---------------- generic keyboard/tap navigation for option lists ---------------- */
  function setNav(buttons, opts) {
    S.nav = { buttons, idx: opts && opts.idx || 0, back: opts && opts.back, grid: opts && opts.grid };
    buttons.forEach((b, i) => {
      b.onclick = (ev) => { ev.stopPropagation(); if (b.classList.contains('dis')) return; S.nav.idx = i; paint(); Audio.sfx('confirm'); b._act && b._act(); };
      b.onmouseenter = () => { if (!b.classList.contains('dis')) { S.nav.idx = i; paint(); } };
    });
    paint();
  }
  function paint() { if (!S.nav) return; S.nav.buttons.forEach((b, i) => b.classList.toggle('sel', i === S.nav.idx)); }
  function navMove(d) {
    const n = S.nav; if (!n || !n.buttons.length) return false;
    let step = d === 'up' ? -1 : d === 'down' ? 1 : 0;
    if (n.grid) { if (d === 'left') step = -1; if (d === 'right') step = 1; if (d === 'up') step = -n.grid; if (d === 'down') step = n.grid; }
    if (!step) return false;
    let i = n.idx;
    for (let k = 0; k < n.buttons.length; k++) {
      i = (i + step + n.buttons.length) % n.buttons.length;
      if (!n.buttons[i].classList.contains('dis')) break;
    }
    n.idx = i; paint(); Audio.sfx('cursor');
    const b = n.buttons[i]; if (b.scrollIntoView) b.scrollIntoView({ block: 'nearest' });
    return true;
  }
  function navOk() { const n = S.nav; if (!n) return false; const b = n.buttons[n.idx]; if (b && !b.classList.contains('dis')) { Audio.sfx('confirm'); b._act && b._act(); } return true; }
  function navBack() { const n = S.nav; if (n && n.back) { Audio.sfx('cancel'); n.back(); return true; } return false; }
  function mkOpt(text, act, cls) {
    const b = document.createElement('button'); b.className = 'opt' + (cls ? ' ' + cls : ''); b.textContent = text; b._act = act; return b;
  }

  function choose(options) {
    if (window.AUTO) {
      const c = window.AUTO_CHOICE;
      return Promise.resolve(typeof c === 'function' ? c(options) : (c || 0));
    }
    return new Promise(res => {
      const box = $('choice'); box.innerHTML = ''; box.classList.remove('hidden');
      const btns = options.map((o, i) => mkOpt(fmt(o.text), () => { box.classList.add('hidden'); S.nav = null; res(i); }));
      btns.forEach(b => box.appendChild(b));
      setNav(btns);
    });
  }

  /* ---------------- effects ---------------- */
  function fade(mode, ms) {
    const f = $('fade');
    ms = window.AUTO ? 1 : (ms || 450);
    f.style.transition = `opacity ${ms}ms`;
    f.classList.toggle('white', mode === 'white');
    f.style.opacity = (mode === 'out' || mode === 'white') ? '1' : '0';
    return sleep(ms + 30);
  }
  function cg(name) {
    const el = $('cg');
    if (!name || name === 'off') { el.classList.add('hidden'); return; }
    el.querySelector('img').src = `assets/cg/${name}.png`;
    el.classList.remove('hidden');
  }
  function titleCard(text) {
    if (window.AUTO) return Promise.resolve();
    const el = $('titlecard'); el.textContent = text; el.classList.remove('hidden');
    el.style.animation = 'none'; void el.offsetWidth; el.style.animation = '';
    return sleep(2800).then(() => el.classList.add('hidden'));
  }
  let toastT = null;
  function toast(text, ms) {
    const el = $('toast'); el.textContent = text; el.classList.remove('hidden');
    clearTimeout(toastT); toastT = setTimeout(() => el.classList.add('hidden'), ms || 2600);
  }
  let hudT = null;
  function mapName(name) {
    const h = $('hud'); $('hud-map').textContent = name; h.classList.remove('hidden'); h.style.opacity = '1';
    clearTimeout(hudT); hudT = setTimeout(() => { h.style.opacity = '0'; }, 2600);
  }
  let loadT = null;
  function loading(on) {
    clearTimeout(loadT);
    if (on) loadT = setTimeout(() => $('loadnote').classList.remove('hidden'), 350);
    else $('loadnote').classList.add('hidden');
  }
  function shake() { const s = $('stage'); s.classList.remove('shake'); void s.offsetWidth; s.classList.add('shake'); setTimeout(() => s.classList.remove('shake'), 480); }
  function flash() { const f = $('flash'); f.classList.remove('on'); void f.offsetWidth; f.classList.add('on'); }

  /* ---------------- name entry ---------------- */
  function askName() {
    if (window.AUTO) return Promise.resolve();
    return new Promise(res => {
      const box = $('namebox'), inp = $('name-input');
      box.classList.remove('hidden'); G.mode = 'name';
      inp.value = G.name || '林恩';
      setTimeout(() => inp.focus(), 50);
      const done = () => {
        const v = inp.value.trim().replace(/[{}<>]/g, '').slice(0, 6);
        G.name = v || '林恩';
        box.classList.add('hidden'); inp.blur(); G.mode = 'scene'; res();
      };
      $('name-ok').onclick = (e) => { e.stopPropagation(); done(); };
      inp.onkeydown = (e) => { e.stopPropagation(); if (e.key === 'Enter') done(); };
    });
  }

  /* ---------------- title ---------------- */
  function showTitle(handlers) {
    G.mode = 'title';
    $('title').classList.remove('hidden');
    ['hud', 'menu-btn', 'dlg', 'choice', 'battle', 'menu', 'panel'].forEach(id => $(id).classList.add('hidden'));
    cg('off');
    const menu = $('title-menu'); menu.innerHTML = '';
    const auto = readSave(AUTO_KEY);
    const got = Object.keys(G.global.codex || {}).length;
    const ends = Object.keys(G.global.endings || {}).map(n => ['', '一', '二', '三'][n]).join(' ');
    const opts = [
      mkOpt('开始新的旅程', handlers.newGame),
      mkOpt(auto ? '继续旅程' : '继续旅程（无记录）', handlers.cont, auto ? '' : 'dis'),
      mkOpt('读取存档', () => handlers.load()),
      mkOpt(`思想手记（${got}/${window.CODEX.length}）`, () => codexPanel(() => showTitle(handlers), true)),
      mkOpt('设置', () => settingsPanel(() => showTitle(handlers))),
    ];
    opts.forEach(b => menu.appendChild(b));
    if (ends) { const p = document.createElement('p'); p.className = 'sub'; p.style.margin = '0.8em 0 0'; p.textContent = `已见结局：${ends}`; menu.appendChild(p); }
    setNav(opts.filter(b => true), { idx: auto ? 1 : 0 });
    Audio.play('title');
  }
  function hideTitle() { $('title').classList.add('hidden'); S.nav = null; }

  /* ---------------- in-game menu ---------------- */
  function openMenu() {
    if (G.mode !== 'map') return;
    G.mode = 'menu';
    const m = $('menu'); m.innerHTML = ''; m.classList.remove('hidden');
    const close = () => { m.classList.add('hidden'); $('panel').classList.add('hidden'); S.nav = null; G.mode = 'map'; };
    const back = () => openMenuAgain();
    const opts = [
      mkOpt('宝物', () => { m.classList.add('hidden'); itemsPanel(back); }),
      mkOpt('思想手记', () => { m.classList.add('hidden'); codexPanel(back); }),
      mkOpt('交谈', () => { close(); if (G.party.length) Script.run(pickPage(PARTY_TALK)); else Script.runInline([{ t: 'narr', text: '身边没有人。' }]); }),
      mkOpt('存档', () => { m.classList.add('hidden'); savePanel(back, true); }),
      mkOpt('读档', () => { m.classList.add('hidden'); savePanel(back, false); }),
      mkOpt('设置', () => { m.classList.add('hidden'); settingsPanel(back); }),
      mkOpt('回到标题', () => { close(); Main.toTitle(); }),
      mkOpt('关闭', close),
    ];
    opts.forEach(b => m.appendChild(b));
    setNav(opts, { back: close });
    function openMenuAgain() { $('panel').classList.add('hidden'); G.mode = 'map'; openMenu(); }
  }

  function panel(title, bodyEl, footText, back) {
    const p = $('panel'); p.innerHTML = ''; p.classList.remove('hidden');
    const h = document.createElement('h2'); h.textContent = title; p.appendChild(h);
    const body = document.createElement('div'); body.className = 'panel-body'; body.appendChild(bodyEl); p.appendChild(body);
    const foot = document.createElement('div'); foot.className = 'panel-foot'; p.appendChild(foot);
    const row = document.createElement('div'); row.className = 'btnrow';
    const bk = document.createElement('button'); bk.className = 'btn'; bk.textContent = '返回'; bk._act = back; row.appendChild(bk);
    if (footText) foot.textContent = footText;
    p.appendChild(row);
    return { p, body, bk };
  }

  function iconCanvas(idx) {
    const c = document.createElement('canvas'); c.width = 16; c.height = 16;
    const im = img('assets/items.png');
    if (im) c.getContext('2d').drawImage(im, idx * 16, 0, 16, 16, 0, 0, 16, 16);
    return c;
  }
  function itemsPanel(back) {
    const wrap = document.createElement('div');
    const ids = Object.keys(G.items).filter(k => G.items[k] > 0 && window.ITEMS[k]);
    if (!ids.length) wrap.textContent = '还没有宝物。';
    ids.forEach(k => {
      const it = window.ITEMS[k];
      const row = document.createElement('div'); row.className = 'item-row';
      row.appendChild(iconCanvas(it.icon));
      const t = document.createElement('div');
      t.innerHTML = `<div class="nm">${it.name}${k === 'coin' ? ' ×' + G.items[k] : ''}</div><div class="ds">${it.desc}</div>`;
      row.appendChild(t); wrap.appendChild(row);
    });
    const { body, bk } = panel('宝物', wrap, `共 ${ids.length} 件`, back);
    setNav([bk], { back });
    S.scrollEl = body;
  }

  function codexPanel(back, fromTitle) {
    const known = fromTitle ? G.global.codex : G.codex;
    const wrap = document.createElement('div');
    const btns = [];
    let grp = '';
    window.CODEX.forEach((e, i) => {
      if (e.group !== grp) { grp = e.group; const g = document.createElement('div'); g.className = 'codex-grp'; g.textContent = grp; wrap.appendChild(g); }
      const ok = !!known[e.id];
      const b = document.createElement('button');
      b.className = 'codex-item opt' + (ok ? '' : ' locked dis');
      b.textContent = ok ? e.title : '？？？';
      b._act = () => codexView(e, () => codexPanel(back, fromTitle));
      wrap.appendChild(b); btns.push(b);
    });
    const n = Object.keys(known).length;
    const { body, bk } = panel('思想手记', wrap, `已解锁 ${n} / ${window.CODEX.length}　每经历一个关键事件，就会多一篇。`, back);
    btns.push(bk);
    const first = btns.findIndex(b => !b.classList.contains('dis'));
    setNav(btns, { back, idx: first >= 0 ? first : btns.length - 1 });
    S.scrollEl = body;
  }
  function codexView(e, back) {
    const v = document.createElement('div'); v.className = 'codex-view';
    const esc = s => (s || '').replace(/[<>&]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]));
    v.innerHTML = `<div class="de">${esc(e.de)}</div><div class="src">${esc(e.src)}</div>` +
      e.body.map(p => `<p>${esc(p)}</p>`).join('') +
      (e.game ? `<p><span class="lab">在游戏里：</span>${esc(e.game)}</p>` : '') +
      (e.ai ? `<p class="ai"><span class="lab">关于人工智能：</span>${esc(e.ai)}</p>` : '');
    const { body, bk } = panel(e.title, v, '', back);
    setNav([bk], { back });
    S.scrollEl = body;
  }

  function savePanel(back, isSave) {
    const wrap = document.createElement('div');
    const btns = [];
    const keys = isSave ? SAVE_KEYS : [AUTO_KEY].concat(SAVE_KEYS);
    keys.forEach((k, i) => {
      const s = readSave(k);
      const label = (k === AUTO_KEY ? '自动记录' : `记录 ${isSave ? i + 1 : i}`) + '　' + describeSave(s);
      const b = mkOpt(label, () => {
        if (isSave) { writeSave(k); toast('已记录。'); savePanel(back, isSave); }
        else if (s) { $('panel').classList.add('hidden'); S.nav = null; Main.loadFrom(s); }
      }, (!isSave && !s) ? 'dis' : '');
      wrap.appendChild(b); btns.push(b);
    });
    const { bk } = panel(isSave ? '存档' : '读档', wrap, isSave ? '进度保存在这台设备的浏览器里。' : '', back);
    btns.push(bk);
    setNav(btns, { back });
  }

  function settingsPanel(back) {
    const wrap = document.createElement('div');
    const btns = [];
    const rows = [
      ['文字速度', () => ['', '慢', '中', '快'][G.settings.speed], () => { G.settings.speed = G.settings.speed % 3 + 1; }],
      ['音乐音量', () => `${Math.round(G.settings.bgm * 10)}`, () => { G.settings.bgm = Math.round((G.settings.bgm * 10 + 1) % 11) / 10; Audio.setVolumes(); }],
      ['音效音量', () => `${Math.round(G.settings.sfx * 10)}`, () => { G.settings.sfx = Math.round((G.settings.sfx * 10 + 1) % 11) / 10; Audio.setVolumes(); Audio.sfx('confirm'); }],
    ];
    rows.forEach(([name, val, act]) => {
      const b = mkOpt('', null); b.classList.add('set-row');
      const paintRow = () => { b.textContent = `${name}　${val()}`; };
      b._act = () => { act(); paintRow(); saveGlobal(); };
      paintRow(); wrap.appendChild(b); btns.push(b);
    });
    const { bk } = panel('设置', wrap, '按确认键切换。', back);
    btns.push(bk);
    setNav(btns, { back });
  }

  /* ---------------- credits ---------------- */
  function credits(n) {
    if (window.AUTO) return Promise.resolve();
    return new Promise(res => {
      const names = ['', '回声', '凡人', '澄明'];
      const el = document.createElement('div'); el.className = 'credits';
      el.innerHTML = `<div class="roll">
        <p style="font-size:1.4em;color:#fff3cf">林中路</p><p>结局${['', '一', '二', '三'][n]} · ${names[n]}</p>
        <h3>剧本 · 美术 · 程序 · 音乐</h3><p>与 AI 一起完成</p>
        <h3>出品</h3><p>Fanshaoliu</p>
        <h3>思想来源</h3><p>马丁·海德格尔</p><p>《存在与时间》《林中路》《技术的追问》</p><p>《筑·居·思》《物》《泰然任之》</p><p>荷尔德林的诗</p>
        <h3>字体</h3><p>Fusion Pixel Font（SIL OFL 1.1）</p>
        <h3>参考</h3><p>SFC《勇者斗恶龙 VI》的地图与城镇布局</p>
        <p style="margin-top:3em">谢谢你走完这条林中路。</p>
        <p>另外两个结局，也许在同一个地方等着你。</p>
        <p style="margin-top:3em;color:#f6cc5a">你在吗？</p></div>
        <div class="skip">点击或按确认键跳过</div>`;
      $('stage').appendChild(el);
      Audio.play('title');
      let done = false;
      const finish = () => { if (done) return; done = true; el.remove(); S.creditsSkip = null; res(); };
      S.creditsSkip = finish;
      el.onclick = finish;
      setTimeout(finish, 43000);
    });
  }

  return {
    say, advance, hideDialog, dialogActive, choose, fade, cg, titleCard, toast, mapName, shake, flash, askName,
    showTitle, hideTitle, openMenu, navMove, navOk, navBack, get nav() { return S.nav; }, clearNav() { S.nav = null; },
    get scrollEl() { return S.scrollEl; }, credits, get creditsSkip() { return S.creditsSkip; }, mkOpt, setNav, iconCanvas,
    loading, portraits: () => [...PORTRAITS],
  };
})();
