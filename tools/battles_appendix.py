"""Write script/appendix_battles.md: every 心象对决 in readable screenplay form, generated from data/battles.js."""
import json, re

src = open('data/battles.js', encoding='utf-8').read()
B = json.loads(src[src.index('{'):src.rindex('}') + 1])
s = open('data/story.js', encoding='utf-8').read()
codex = {c['id']: c['title'] for c in json.loads(s[s.index('window.CODEX = ') + 15:].rstrip().rstrip(';'))}
items = open('data/items.js', encoding='utf-8').read()
ITEMS = {k: v['name'] for k, v in json.loads(items[items.index('{'):items.rindex('}') + 1]).items()}

LABEL = {'ask': '追问', 'listen': '倾听', 'silence': '沉默', 'wait': '等待', 'act': '动手', 'item': '宝物（其他）',
         'teleport': '克洛伊·移位', 'analyze': '罐头·分析', 'moment': '眼下', 'attack': '攻击', 'flee': '逃跑', 'call': '呼唤'}
ORDER = ['ask', 'listen', 'silence', 'wait', 'moment', 'act', 'attack', 'flee', 'call', 'teleport', 'analyze', 'item']
WHERE = {
    'slime': '第二章 · 林中路', 'wolf': '第二章 · 林中路', 'bat': '第三章 · 去钟港的路上', 'mask': '第三章 · 钟港小巷',
    'giant': '第三章 · 钟楼顶层', 'sentinel': '第四章 · 学院档案库', 'nothing': '第五章 · 无之回廊', 'noone': '第五章 · 第一回声站',
}
KEY = {
    'slime': '追问。闲言说不出第一个说这话的人，一问来源它就瘪下去。认真倾听反而喂大了它。',
    'wolf': '动手，正面迎上去；或者举起伊斯特的灯。怕总是怕某个确定的东西，看清了，它就只是一堆别人的字。',
    'bat': '等待。别追它，站住，看一朵花看很久。好奇从不在任何东西上停留。',
    'mask': '动手，去做一件实际的事；霍夫的锤子也行。两可什么都「早就知道」，唯独占不了一件已经做完的事。',
    'giant': '一直等待，等到最深处，指令「眼下」才会出现。深度的无聊把一切都推开，只剩下你为什么站在这里。',
    'sentinel': '宝物：空壶、诗人的残页、霍夫的锤子、旧照片、桥钉，外加沉默。守卫能把一切归类为储备，归不了物和诗。',
    'nothing': '不攻击，不逃跑，等待；呼唤克洛伊能稳住心绪。畏没有对象，打不到，也逃不掉，只能从里面走过去。',
    'noone': '分三段。先用追问、沉默、倾听削弱它；格斯特被吞进去以后，让克洛伊冒险移位，让罐头拒绝回去；最后它学会了你们的每一招，这时什么都不再做，只是等待，林恩会第一次开口。',
}


def fmt(t):
    return t.replace('{林恩}', '林恩')


def lines(resp, indent='  '):
    out = []
    for i, r in enumerate(resp):
        head = f'{indent}{"第" + str(i + 1) + "次" if len(resp) > 1 else ""}'
        body = ' / '.join(fmt(x) for x in r['t'])
        out.append(f'{indent}- {("（" + head.strip() + "）") if head.strip() else ""}{body}')
    return out


out = ['# 附录 · 心象对决', '',
       '> 游戏里的战斗叫「心象对决」。敌人是某种生存状态的化身，打不死，只能被理解。下面是八场对决的全部台词，',
       '> 按指令分组；同一个指令多次使用，回应会变化。「声势」是敌人的气势条，「心绪」是队伍的状态，心绪耗尽就只能先退开。', '']
for bid, b in B.items():
    title = b.get('name') or '（无名）'
    out += [f'## {title}', '', f'- 地点：{WHERE.get(bid, "")}',
            f'- 关联手记：{"、".join(codex.get(c, c) for c in b.get("codex", [])) or "（无）"}',
            f'- 解法：{KEY.get(bid, "")}', '']
    out += ['**登场**', ''] + [f'> {fmt(x)}' for x in b['intro']] + ['']

    def dump_cmds(cmds, itemsd, heading):
        res = [heading, ''] if heading else []
        for k in ORDER:
            if k in cmds:
                res.append(f'- **{LABEL[k]}**')
                res += lines(cmds[k])
        for k, v in (itemsd or {}).items():
            res.append(f'- **宝物·{ITEMS.get(k, k)}**')
            res += lines(v)
        return res + ['']
    out += dump_cmds(b['cmds'], b.get('items'), '**指令与回应**')
    for i, ph in enumerate(b.get('phases') or []):
        if i == 0 and not ph.get('cmds'):
            continue
        out += [f'**第 {i + 1} 阶段**', '']
        if ph.get('enter'):
            out += [f'> {fmt(x)}' for x in ph['enter']] + ['']
        if ph.get('cmds') or ph.get('items'):
            out += dump_cmds(ph.get('cmds', {}), ph.get('items'), '')
    enemy = b.get('enemy') or []
    if enemy:
        out += ['**敌方行动**', ''] + [f'- {" / ".join(fmt(x) for x in e["t"])}' for e in enemy] + ['']
    if b.get('retreatText'):
        out += ['**心绪见底时**', ''] + [f'> {fmt(x)}' for x in b['retreatText']] + ['']
    if b.get('speakLine'):
        out += ['**终幕**', '', f'> 林恩：{b["speakLine"]}', '']
    if b.get('win'):
        out += ['**胜利**', ''] + [f'> {fmt(x)}' for x in b['win']] + ['']
    out += ['---', '']
open('script/appendix_battles.md', 'w', encoding='utf-8').write('\n'.join(out))
print('appendix written:', len(B), 'battles,', sum(len(x) for x in out), 'chars')
